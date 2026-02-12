---
name: fastapi-logging
description: Configure structured JSON logging with correlation IDs and request context for FastAPI
---

# FastAPI Logging & Correlation IDs

## Overview

This skill covers setting up structured JSON logging with correlation ID middleware for request tracing across the application.

## Create logging.py

Create `src/app/logging.py`:

```python
import logging
import sys
from typing import Any

from pythonjsonlogger import jsonlogger

from app.config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that adds standard fields to all log records.
    
    Output format:
    {
        "timestamp": "2025-01-05T12:00:00.000Z",
        "level": "INFO",
        "message": "Request completed",
        "logger": "app.api.v1.items",
        "correlation_id": "uuid",
        ...additional fields
    }
    """

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)

        # Standard fields
        log_record["timestamp"] = self.formatTime(record, self.datefmt)
        log_record["level"] = record.levelname
        log_record["logger"] = record.name

        # Remove default fields we're replacing
        log_record.pop("levelname", None)
        log_record.pop("name", None)

        # Add correlation_id from context if available
        from app.middleware.correlation_id import get_correlation_id

        correlation_id = get_correlation_id()
        if correlation_id:
            log_record["correlation_id"] = correlation_id


def setup_logging() -> None:
    """
    Configure application logging.
    
    Call this early in application startup, before creating the FastAPI app.
    
    Configures:
    - JSON format for production (LOG_JSON_FORMAT=true)
    - Human-readable format for development
    - Log level from settings
    - Suppresses noisy third-party loggers
    """
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    if settings.log_json_format:
        # JSON format for production
        formatter = CustomJsonFormatter(
            fmt="%(timestamp)s %(level)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S.%f",
        )
    else:
        # Human-readable format for development
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.database_echo else logging.WARNING
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Usage:
        logger = get_logger(__name__)
        logger.info("Something happened", extra={"user_id": "123"})
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
```

## Create middleware/correlation_id.py

Create `src/app/middleware/correlation_id.py`:

```python
import contextvars
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Context variable to store correlation ID for the current request
_correlation_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "correlation_id",
    default=None,
)

# Header name for correlation ID
CORRELATION_ID_HEADER = "X-Correlation-ID"


def get_correlation_id() -> str | None:
    """
    Get the correlation ID for the current request context.
    
    Returns None if called outside of a request context.
    
    Usage:
        from app.middleware.correlation_id import get_correlation_id
        
        correlation_id = get_correlation_id()
        logger.info("Processing", extra={"correlation_id": correlation_id})
    """
    return _correlation_id_ctx.get()


def set_correlation_id(correlation_id: str) -> None:
    """
    Set the correlation ID for the current context.
    
    Typically called by middleware, but can be used in tests
    or background tasks.
    """
    _correlation_id_ctx.set(correlation_id)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware that manages correlation IDs for request tracing.
    
    Behavior:
    1. Checks for X-Correlation-ID header in incoming request
    2. If present, uses that ID (for distributed tracing)
    3. If absent, generates a new UUID
    4. Stores ID in context variable (accessible via get_correlation_id())
    5. Adds ID to response headers
    
    This enables tracing requests across:
    - Multiple services (when ID is passed in headers)
    - Log aggregation systems
    - Error tracking systems
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # Get correlation ID from header or generate new one
        correlation_id = request.headers.get(CORRELATION_ID_HEADER)
        if not correlation_id:
            correlation_id = str(uuid4())

        # Store in context variable
        set_correlation_id(correlation_id)

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers[CORRELATION_ID_HEADER] = correlation_id

        return response
```

## Create middleware/__init__.py

Create `src/app/middleware/__init__.py`:

```python
from app.middleware.correlation_id import (
    CORRELATION_ID_HEADER,
    CorrelationIdMiddleware,
    get_correlation_id,
    set_correlation_id,
)

__all__ = [
    "CORRELATION_ID_HEADER",
    "CorrelationIdMiddleware",
    "get_correlation_id",
    "set_correlation_id",
]
```

## Usage in Application

### In main.py

```python
from app.logging import setup_logging
from app.middleware import CorrelationIdMiddleware

# Setup logging BEFORE creating app
setup_logging()

def create_app() -> FastAPI:
    app = FastAPI(...)
    
    # Add correlation ID middleware
    app.add_middleware(CorrelationIdMiddleware)
    
    return app
```

### In Services/Routers

```python
from app.logging import get_logger

logger = get_logger(__name__)

class ItemService:
    async def create(self, obj_in: ItemCreate) -> Item:
        logger.info(
            "Creating item",
            extra={
                "item_name": obj_in.name,
                "category_id": str(obj_in.category_id),
            },
        )
        
        item = await self._repository.create(obj_in)
        
        logger.info(
            "Item created successfully",
            extra={"item_id": str(item.id)},
        )
        
        return item
```

### In Exception Handlers

```python
from app.middleware.correlation_id import get_correlation_id

async def app_exception_handler(request: Request, exc: AppException):
    correlation_id = get_correlation_id()
    
    logger.warning(
        "Application error",
        extra={
            "error_code": exc.error_code,
            "correlation_id": correlation_id,
        },
    )
    
    return JSONResponse(
        content={
            "detail": exc.message,
            "correlation_id": correlation_id,
            ...
        }
    )
```

## Log Output Examples

### JSON Format (Production)

```json
{
  "timestamp": "2025-01-05T12:00:00.123456",
  "level": "INFO",
  "logger": "app.items.service",
  "message": "Creating item",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "item_name": "Widget",
  "category_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

### Human-Readable Format (Development)

```
2025-01-05 12:00:00 | INFO     | app.items.service | Creating item
```

## Logging Best Practices

### 1. Use Appropriate Log Levels

| Level | Use Case |
|-------|----------|
| `DEBUG` | Detailed diagnostic information |
| `INFO` | Routine operations, state changes |
| `WARNING` | Unexpected but handled situations |
| `ERROR` | Errors that need attention |
| `CRITICAL` | System failures |

### 2. Include Contextual Information

```python
# Good - includes context
logger.info(
    "Order processed",
    extra={
        "order_id": str(order.id),
        "total": order.total,
        "items_count": len(order.items),
    },
)

# Bad - no context
logger.info("Order processed")
```

### 3. Log at Boundaries

- Log at entry/exit of services
- Log external API calls
- Log database operations (sparingly)

### 4. Don't Log Sensitive Data

```python
# Bad - logs password
logger.info(f"User login: {user.email}, password: {user.password}")

# Good - no sensitive data
logger.info("User login attempt", extra={"email": user.email})
```

### 5. Use Structured Fields

```python
# Good - structured
logger.error(
    "Database query failed",
    extra={
        "query": "SELECT * FROM items",
        "duration_ms": 1500,
        "error": str(e),
    },
)

# Bad - unstructured
logger.error(f"Database query failed: {e}")
```

## Request Logging Middleware (Optional)

For detailed request/response logging:

```python
import time
from app.logging import get_logger

logger = get_logger("app.http")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        
        response = await call_next(request)
        
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        logger.info(
            "Request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )
        
        return response
```
