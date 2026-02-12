from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import configure_logging
from app.core.logging.middleware import WideEventMiddleware
from app.middlewares.context import RequestContextMiddleware

from .routers import get_app_router


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
    add_sentry: bool = settings.ENVIRONMENT != "local",
) -> FastAPI:
    # Configure logging early
    configure_logging()

    app = FastAPI(lifespan=lifespan)

    # WideEventMiddleware FIRST (outermost) - handles request logging
    app.add_middleware(WideEventMiddleware)  # type: ignore[invalid-argument-type]

    # RequestContextMiddleware sets request_id in context
    app.add_middleware(RequestContextMiddleware)  # type: ignore[invalid-argument-type]

    app.add_middleware(
        CORSMiddleware,  # type: ignore[invalid-argument-type]
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
    def sanity_check() -> str:
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
