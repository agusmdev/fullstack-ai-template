from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sentry_sdk.scrubber import DEFAULT_DENYLIST, EventScrubber
from sentry_sdk.types import Event, Hint
from sqlalchemy.exc import DBAPIError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging import configure_logging
from app.core.logging.middleware import WideEventMiddleware
from app.core.logging.sanitizer import (
    SENSITIVE_KEYS,
    SENSITIVE_QUERY_PARAMS,
    sanitize_query_string,
)
from app.exceptions import ErrorResponse

from .routers import get_app_router

# Sentry's EventScrubber matches exact key names only ("new_password" is not
# "password"), so add this app's secret names to its denylist.
_SENTRY_DENYLIST = sorted(
    {
        *DEFAULT_DENYLIST,
        *SENSITIVE_KEYS,
        *SENSITIVE_QUERY_PARAMS,
        "new_password",
        "raw_password",
    }
)


def _scrub_sentry_event(event: Event, _hint: Hint) -> Event:
    """Redact credentials in the request query string (e.g. the OAuth ``code``)."""
    request = event.get("request")
    if request and isinstance(request.get("query_string"), str):
        request["query_string"] = sanitize_query_string(request["query_string"])
    return event


async def _http_exception_handler(
    _request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Surface error_code alongside detail for all HTTP exceptions.

    Registered for Starlette's HTTPException (the base of FastAPI's), so the
    router's own 404 (unknown path) and 405 (wrong method) follow the contract
    too. Built through the ``ErrorResponse`` contract so the response shape is
    validated by the schema rather than hand-rolled per call site.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            detail=exc.detail,
            error_code=getattr(exc, "error_code", "http_error"),
        ).model_dump(mode="json"),
        headers=exc.headers,
    )


async def _validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return 422 with FastAPI's list of issues in ``detail`` plus an error_code."""
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            detail=jsonable_encoder(exc.errors()),
            error_code="validation_error",
        ).model_dump(mode="json"),
    )


# Postgres SQLSTATE class 22, "data exception": the database cannot store a
# value the client sent. The usual case is a NUL character (22021) in a text
# field: JSON allows "\u0000", Postgres text does not.
_DATA_EXCEPTION_CLASS = "22"
_DATA_EXCEPTION_DETAILS = {"22021": "Text must not contain NUL characters"}


async def _database_error_handler(_request: Request, exc: DBAPIError) -> JSONResponse:
    """Return 422 when Postgres rejects a value from the request.

    Other database errors are server faults: they are re-raised, and
    WideEventMiddleware turns them into a logged JSON 500.
    """
    sqlstate = getattr(exc.orig, "sqlstate", None) or ""
    if not sqlstate.startswith(_DATA_EXCEPTION_CLASS):
        raise exc
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            detail=_DATA_EXCEPTION_DETAILS.get(
                sqlstate, "A value in the request cannot be stored"
            ),
            error_code="validation_error",
        ).model_dump(mode="json"),
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown events.

    The database engine is created on first use via get_engine() in app/dependencies,
    which uses lru_cache to ensure singleton behavior. This lifespan function
    ensures the engine is properly disposed on shutdown.
    """
    # Trigger engine creation to verify database connection during startup
    from app.dependencies import get_engine

    engine = get_engine()

    yield

    # Shutdown: Close database connections
    await engine.dispose()


def create_app(
    add_sentry: bool | None = None,
) -> FastAPI:
    if add_sentry is None:
        add_sentry = settings.ENVIRONMENT != "local"

    # Configure logging early
    configure_logging()

    app = FastAPI(lifespan=lifespan)
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
    app.add_exception_handler(DBAPIError, _database_error_handler)

    # Middleware is applied LIFO: last-added = outermost (first to handle request).
    # Order: CORS → WideEvent. WideEventMiddleware generates the canonical
    # request_id and emits the wide log.
    app.add_middleware(WideEventMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            settings.FRONTEND_URL,
            "http://localhost:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["content-disposition"],
    )

    app_router = get_app_router()

    @app_router.get("/health")
    def health_check() -> str:
        return "FastAPI running!"

    if add_sentry:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            # Frame locals and request bodies hold plaintext passwords and
            # tokens (reset_password(token, new_password), raw_password).
            # Never send locals, cookies or user IPs, and scrub the extra
            # secret names that Sentry's default denylist does not know.
            include_local_variables=False,
            send_default_pii=False,
            event_scrubber=EventScrubber(
                denylist=_SENTRY_DENYLIST,
                recursive=True,
            ),
            before_send=_scrub_sentry_event,
            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for performance monitoring.
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            # Set profiles_sample_rate to 1.0 to profile 100%
            # of sampled transactions.
            # We recommend adjusting this value in production.
            profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
        )

    app.include_router(app_router)
    return app
