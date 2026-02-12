---
name: fastapi-app-factory
description: Create FastAPI application factory with lifespan, middleware, pagination, and router configuration
---

# FastAPI Application Factory

## Overview

This skill covers creating the FastAPI application factory pattern with proper lifespan management, middleware registration, pagination setup, and router configuration.

## Create main.py

Create `src/app/main.py`:

```python
import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi_pagination import add_pagination

from app.api import api_router
from app.config import settings
from app.database import engine
from app.exception_handlers import register_exception_handlers
from app.logging import setup_logging
from app.middleware import CorrelationIdMiddleware

# Setup logging before anything else
setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.
    
    Handles startup and shutdown events:
    - Startup: Log application start, initialize resources
    - Shutdown: Close database connections, cleanup resources
    
    This replaces the deprecated @app.on_event decorators.
    """
    # Startup
    logger.info(
        "Starting application",
        extra={
            "app_name": settings.app_name,
            "debug": settings.debug,
        },
    )

    yield

    # Shutdown
    logger.info("Shutting down application")
    await engine.dispose()
    logger.info("Database connections closed")


def create_app() -> FastAPI:
    """
    Application factory function.
    
    Creates and configures the FastAPI application with:
    - Lifespan management
    - Exception handlers
    - Middleware (correlation ID)
    - Pagination support
    - API routers
    
    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
        # OpenAPI configuration
        openapi_url="/api/openapi.json" if settings.debug else None,
        docs_url="/api/docs" if settings.debug else None,
        redoc_url="/api/redoc" if settings.debug else None,
    )

    # Register exception handlers
    register_exception_handlers(app)

    # Add middleware (order matters - first added = outermost)
    app.add_middleware(CorrelationIdMiddleware)

    # Add pagination support
    add_pagination(app)

    # Include routers
    app.include_router(api_router, prefix="/api")

    return app


# Create the application instance
app = create_app()
```

## Create api/__init__.py

Create `src/app/api/__init__.py`:

```python
from fastapi import APIRouter

from app.api.v1 import router as v1_router

api_router = APIRouter()

# Include versioned routers
api_router.include_router(v1_router, prefix="/v1")


@api_router.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """
    Health check endpoint.
    
    Returns a simple status indicating the API is running.
    Use this for load balancer health checks.
    """
    return {"status": "healthy"}
```

## Create api/v1/__init__.py

Create `src/app/api/v1/__init__.py`:

```python
from fastapi import APIRouter

# Import entity routers here
# from app.items.router import router as items_router
# from app.users.router import router as users_router

router = APIRouter()

# Include entity routers
# router.include_router(items_router)
# router.include_router(users_router)
```

## Create api/v1/router.py (Alternative)

If you prefer a separate router file:

```python
# src/app/api/v1/router.py
from fastapi import APIRouter

# Import entity routers
# from app.items.router import router as items_router

router = APIRouter()

# Include entity routers
# router.include_router(items_router)
```

## Running the Application

### Development

```bash
# Using uvicorn directly
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or with more options
uv run uvicorn app.main:app \
    --reload \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info
```

### Production

```bash
# Using uvicorn with workers
uv run uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level warning

# Or with gunicorn + uvicorn workers
uv run gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 4 \
    --bind 0.0.0.0:8000
```

## Application Configuration Options

### FastAPI Constructor Options

```python
app = FastAPI(
    # Basic
    title="My API",
    description="API description",
    version="1.0.0",
    debug=settings.debug,
    
    # Lifespan
    lifespan=lifespan,
    
    # OpenAPI/Docs
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_tags=[
        {"name": "items", "description": "Item operations"},
        {"name": "users", "description": "User operations"},
    ],
    
    # Response configuration
    default_response_class=JSONResponse,
    
    # Root path for reverse proxy
    root_path="/api",
)
```

### Conditional OpenAPI

```python
# Disable OpenAPI in production
openapi_url="/api/openapi.json" if settings.debug else None,
docs_url="/api/docs" if settings.debug else None,
redoc_url=None,  # Disable ReDoc entirely
```

## Middleware Order

Middleware is executed in reverse order of addition (first added = outermost):

```python
# Request flow: CorrelationID -> RequestLogging -> ... -> Router
# Response flow: Router -> ... -> RequestLogging -> CorrelationID

app.add_middleware(CorrelationIdMiddleware)  # Outermost
app.add_middleware(RequestLoggingMiddleware)  # Inner
```

## Adding CORS (if needed)

```python
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    app = FastAPI(...)
    
    # Add CORS before other middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  # Or ["*"] for all
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Then other middleware
    app.add_middleware(CorrelationIdMiddleware)
    
    return app
```

## Adding Custom Request State

```python
from starlette.middleware.base import BaseHTTPMiddleware

class RequestStateMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Add custom state to request
        request.state.start_time = time.time()
        request.state.request_id = str(uuid4())
        
        response = await call_next(request)
        return response
```

## Application Structure Summary

```
main.py (create_app)
    │
    ├── Lifespan (startup/shutdown)
    │
    ├── Exception Handlers
    │   └── register_exception_handlers(app)
    │
    ├── Middleware
    │   └── CorrelationIdMiddleware
    │
    ├── Pagination
    │   └── add_pagination(app)
    │
    └── Routers
        └── api_router (/api)
            ├── /health
            └── v1_router (/api/v1)
                ├── items_router (/api/v1/items)
                └── users_router (/api/v1/users)
```

## Health Check Patterns

### Simple Health Check

```python
@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### Detailed Health Check

```python
from sqlalchemy import text
from app.database import async_session_factory

@api_router.get("/health/detailed")
async def detailed_health_check():
    health = {
        "status": "healthy",
        "checks": {}
    }
    
    # Database check
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        health["checks"]["database"] = "healthy"
    except Exception as e:
        health["status"] = "unhealthy"
        health["checks"]["database"] = f"unhealthy: {str(e)}"
    
    return health
```

## Environment-Specific Configuration

```python
def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )
    
    # Development-only features
    if settings.debug:
        # Enable Swagger UI
        app.openapi_url = "/api/openapi.json"
        app.docs_url = "/api/docs"
        
        # Add debug middleware
        from app.middleware.debug import DebugMiddleware
        app.add_middleware(DebugMiddleware)
    
    # ... rest of configuration
    
    return app
```
