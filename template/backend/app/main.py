from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.context import clear_request_context
from app.core.logging import configure_logging
from app.core.logging.middleware import WideEventMiddleware
from app.exceptions import ErrorResponse
from app.middlewares.context import RequestContextMiddleware

from .routers import get_app_router


async def _http_exception_handler(
    _request: Request, exc: HTTPException
) -> JSONResponse:
    """Surface error_code alongside detail for all HTTP exceptions.

    Built through the ``ErrorResponse`` contract so the response shape is
    validated by the schema rather than hand-rolled per call site.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            detail=exc.detail,
            error_code=getattr(exc, "error_code", "http_error"),
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
    app.add_exception_handler(HTTPException, _http_exception_handler)

    # Middleware is applied LIFO: last-added = outermost (first to handle request).
    # Desired order: CORS → WideEvent → RequestContext
    #
    # RequestContextMiddleware reads the request_id from WideEventContext, so it must
    # run AFTER WideEventMiddleware (i.e., be added FIRST = innermost).
    app.add_middleware(RequestContextMiddleware)  # type: ignore[invalid-argument-type]  # FastAPI add_middleware expects Type[_MiddlewareClass] but our custom middleware inherits BaseHTTPMiddleware correctly

    # WideEventMiddleware generates the canonical request_id and emits the wide log.
    # Must wrap RequestContextMiddleware so the ID is set before context middleware runs.
    # Inject clear_request_context so core middleware doesn't import app-level modules.
    app.add_middleware(WideEventMiddleware, on_request_cleanup=clear_request_context)  # type: ignore[invalid-argument-type]  # FastAPI add_middleware expects Type[_MiddlewareClass] but our custom middleware inherits BaseHTTPMiddleware correctly

    app.add_middleware(
        CORSMiddleware,  # type: ignore[invalid-argument-type]  # FastAPI add_middleware expects Type[_MiddlewareClass] but our custom middleware inherits BaseHTTPMiddleware correctly
        allow_origins=[
            settings.FRONTEND_URL,
            "http://localhost:3000",
            "http://localhost:3150",
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
            send_default_pii=True,
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
