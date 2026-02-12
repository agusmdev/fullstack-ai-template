---
name: fastapi-exceptions
description: Create custom exceptions, error response schemas, and centralized exception handlers for FastAPI
---

# FastAPI Exceptions & Error Handling

## Overview

This skill covers creating a comprehensive exception handling system with custom exceptions, standardized error responses, and centralized exception handlers.

## Create exceptions.py

Create `src/app/exceptions.py`:

```python
from typing import Any
from uuid import UUID


class AppException(Exception):
    """
    Base exception for all application errors.
    
    All custom exceptions should inherit from this class.
    Provides consistent error structure across the application.
    
    Attributes:
        message: Human-readable error description
        error_code: Machine-readable error code (e.g., "NOT_FOUND")
        status_code: HTTP status code
        details: Additional error context
    """

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppException):
    """
    Raised when a requested resource is not found.
    
    HTTP Status: 404
    """

    def __init__(
        self,
        resource: str,
        id: UUID | str | None = None,
        field: str | None = None,
        value: Any = None,
    ):
        if id is not None:
            message = f"{resource} with id '{id}' not found"
            details = {"resource": resource, "id": str(id)}
        elif field is not None:
            message = f"{resource} with {field}='{value}' not found"
            details = {"resource": resource, "field": field, "value": str(value)}
        else:
            message = f"{resource} not found"
            details = {"resource": resource}

        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            status_code=404,
            details=details,
        )


class ConflictError(AppException):
    """
    Raised when an operation conflicts with existing data.
    
    Examples:
    - Duplicate unique constraint violation
    - Resource already exists
    - Concurrent modification conflict
    
    HTTP Status: 409
    """

    def __init__(
        self,
        resource: str,
        field: str,
        value: Any,
        message: str | None = None,
    ):
        default_message = f"{resource} with {field}='{value}' already exists"
        super().__init__(
            message=message or default_message,
            error_code="CONFLICT",
            status_code=409,
            details={
                "resource": resource,
                "field": field,
                "value": str(value),
            },
        )


class ValidationError(AppException):
    """
    Raised for business logic validation failures.
    
    Use for validation that goes beyond Pydantic schema validation.
    
    HTTP Status: 422
    """

    def __init__(
        self,
        message: str,
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        error_details = details or {}
        if field:
            error_details["field"] = field

        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details=error_details,
        )


class ForbiddenError(AppException):
    """
    Raised when user lacks permission for an operation.
    
    HTTP Status: 403
    """

    def __init__(
        self,
        message: str = "You do not have permission to perform this action",
        resource: str | None = None,
        action: str | None = None,
    ):
        details = {}
        if resource:
            details["resource"] = resource
        if action:
            details["action"] = action

        super().__init__(
            message=message,
            error_code="FORBIDDEN",
            status_code=403,
            details=details,
        )


class UnauthorizedError(AppException):
    """
    Raised when authentication is required but missing or invalid.
    
    HTTP Status: 401
    """

    def __init__(
        self,
        message: str = "Authentication required",
    ):
        super().__init__(
            message=message,
            error_code="UNAUTHORIZED",
            status_code=401,
        )


class BadRequestError(AppException):
    """
    Raised for malformed or invalid requests.
    
    HTTP Status: 400
    """

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code="BAD_REQUEST",
            status_code=400,
            details=details or {},
        )


class DatabaseError(AppException):
    """
    Raised for database-related errors.
    
    HTTP Status: 500
    
    Note: Be careful not to expose sensitive database information.
    """

    def __init__(
        self,
        message: str = "A database error occurred",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=500,
            details=details or {},
        )


class ServiceUnavailableError(AppException):
    """
    Raised when an external service is unavailable.
    
    HTTP Status: 503
    """

    def __init__(
        self,
        service: str,
        message: str | None = None,
    ):
        super().__init__(
            message=message or f"Service '{service}' is currently unavailable",
            error_code="SERVICE_UNAVAILABLE",
            status_code=503,
            details={"service": service},
        )
```

## Create schemas/error.py

Create `src/app/schemas/error.py`:

```python
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """
    Standardized error response schema.
    
    All API errors return this structure for consistency.
    """

    detail: str = Field(
        ...,
        description="Human-readable error message",
        examples=["Item with id '123' not found"],
    )
    error_code: str = Field(
        ...,
        description="Machine-readable error code",
        examples=["NOT_FOUND", "VALIDATION_ERROR", "CONFLICT"],
    )
    correlation_id: str = Field(
        ...,
        description="Request correlation ID for tracing",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    timestamp: datetime = Field(
        ...,
        description="When the error occurred (UTC)",
    )
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional error context",
        examples=[{"resource": "Item", "id": "123"}],
    )


class ValidationErrorDetail(BaseModel):
    """Detail for a single validation error."""

    loc: list[str | int] = Field(
        ...,
        description="Location of the error (field path)",
        examples=[["body", "name"]],
    )
    msg: str = Field(
        ...,
        description="Error message",
        examples=["field required"],
    )
    type: str = Field(
        ...,
        description="Error type",
        examples=["value_error.missing"],
    )


class ValidationErrorResponse(BaseModel):
    """
    Response schema for Pydantic validation errors.
    
    Maintains compatibility with FastAPI's default validation error format
    while adding correlation_id and timestamp.
    """

    detail: list[ValidationErrorDetail]
    error_code: str = "VALIDATION_ERROR"
    correlation_id: str
    timestamp: datetime
```

## Create exception_handlers.py

Create `src/app/exception_handlers.py`:

```python
import logging
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.exceptions import AppException, ConflictError, DatabaseError
from app.middleware.correlation_id import get_correlation_id
from app.schemas.error import ErrorResponse, ValidationErrorResponse

logger = logging.getLogger(__name__)


async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    """
    Handle all AppException subclasses.
    
    Converts application exceptions to standardized JSON responses.
    """
    correlation_id = get_correlation_id()

    # Log the error
    logger.warning(
        "Application error occurred",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "message": exc.message,
            "details": exc.details,
            "correlation_id": correlation_id,
            "path": str(request.url.path),
        },
    )

    error_response = ErrorResponse(
        detail=exc.message,
        error_code=exc.error_code,
        correlation_id=correlation_id,
        timestamp=datetime.now(UTC),
        details=exc.details,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode="json"),
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle Pydantic/FastAPI validation errors.
    
    Converts validation errors to standardized format while
    preserving the detailed error information.
    """
    correlation_id = get_correlation_id()

    logger.warning(
        "Validation error",
        extra={
            "errors": exc.errors(),
            "correlation_id": correlation_id,
            "path": str(request.url.path),
        },
    )

    error_response = ValidationErrorResponse(
        detail=[
            {
                "loc": list(err["loc"]),
                "msg": err["msg"],
                "type": err["type"],
            }
            for err in exc.errors()
        ],
        correlation_id=correlation_id,
        timestamp=datetime.now(UTC),
    )

    return JSONResponse(
        status_code=422,
        content=error_response.model_dump(mode="json"),
    )


async def pydantic_validation_exception_handler(
    request: Request,
    exc: PydanticValidationError,
) -> JSONResponse:
    """
    Handle raw Pydantic validation errors (not from FastAPI).
    """
    correlation_id = get_correlation_id()

    error_response = ValidationErrorResponse(
        detail=[
            {
                "loc": list(err["loc"]),
                "msg": err["msg"],
                "type": err["type"],
            }
            for err in exc.errors()
        ],
        correlation_id=correlation_id,
        timestamp=datetime.now(UTC),
    )

    return JSONResponse(
        status_code=422,
        content=error_response.model_dump(mode="json"),
    )


async def integrity_error_handler(
    request: Request,
    exc: IntegrityError,
) -> JSONResponse:
    """
    Handle SQLAlchemy IntegrityError (constraint violations).
    
    Attempts to parse the error and return a user-friendly message.
    """
    correlation_id = get_correlation_id()

    logger.error(
        "Database integrity error",
        extra={
            "error": str(exc.orig),
            "correlation_id": correlation_id,
            "path": str(request.url.path),
        },
    )

    # Try to extract constraint name for better error message
    error_str = str(exc.orig)

    # Common patterns for PostgreSQL unique constraint violations
    if "unique constraint" in error_str.lower():
        error_response = ErrorResponse(
            detail="A record with this value already exists",
            error_code="CONFLICT",
            correlation_id=correlation_id,
            timestamp=datetime.now(UTC),
        )
        return JSONResponse(
            status_code=409,
            content=error_response.model_dump(mode="json"),
        )

    # Foreign key violation
    if "foreign key constraint" in error_str.lower():
        error_response = ErrorResponse(
            detail="Referenced record does not exist",
            error_code="VALIDATION_ERROR",
            correlation_id=correlation_id,
            timestamp=datetime.now(UTC),
        )
        return JSONResponse(
            status_code=422,
            content=error_response.model_dump(mode="json"),
        )

    # Generic database error
    error_response = ErrorResponse(
        detail="A database constraint was violated",
        error_code="DATABASE_ERROR",
        correlation_id=correlation_id,
        timestamp=datetime.now(UTC),
    )
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(mode="json"),
    )


async def sqlalchemy_error_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    """
    Handle generic SQLAlchemy errors.
    
    Logs the full error but returns a generic message to avoid
    exposing database internals.
    """
    correlation_id = get_correlation_id()

    logger.error(
        "Database error",
        extra={
            "error": str(exc),
            "correlation_id": correlation_id,
            "path": str(request.url.path),
        },
        exc_info=True,
    )

    error_response = ErrorResponse(
        detail="A database error occurred",
        error_code="DATABASE_ERROR",
        correlation_id=correlation_id,
        timestamp=datetime.now(UTC),
    )

    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(mode="json"),
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Catch-all handler for unhandled exceptions.
    
    Logs the full exception but returns a generic error to the client.
    """
    correlation_id = get_correlation_id()

    logger.exception(
        "Unhandled exception",
        extra={
            "correlation_id": correlation_id,
            "path": str(request.url.path),
        },
    )

    error_response = ErrorResponse(
        detail="An unexpected error occurred",
        error_code="INTERNAL_ERROR",
        correlation_id=correlation_id,
        timestamp=datetime.now(UTC),
    )

    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(mode="json"),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers with the FastAPI app.
    
    Call this in your app factory:
        register_exception_handlers(app)
    """
    # Application exceptions
    app.add_exception_handler(AppException, app_exception_handler)

    # Validation exceptions
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(PydanticValidationError, pydantic_validation_exception_handler)

    # Database exceptions
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)

    # Catch-all (must be last)
    app.add_exception_handler(Exception, unhandled_exception_handler)
```

## Usage Examples

### In Services

```python
from app.exceptions import NotFoundError, ConflictError, ValidationError

class ItemService:
    async def get_by_id_or_raise(self, id: UUID) -> Item:
        item = await self._repository.get_by_id(id)
        if not item:
            raise NotFoundError(resource="Item", id=id)
        return item

    async def create(self, obj_in: ItemCreate) -> Item:
        existing = await self._repository.get_by_name(obj_in.name)
        if existing:
            raise ConflictError(
                resource="Item",
                field="name",
                value=obj_in.name,
            )
        return await self._repository.create(obj_in)

    async def activate(self, id: UUID) -> Item:
        item = await self.get_by_id_or_raise(id)
        if item.is_deleted:
            raise ValidationError(
                message="Cannot activate a deleted item",
                field="deleted_at",
            )
        # ... activation logic
```

### Error Response Examples

**404 Not Found:**
```json
{
  "detail": "Item with id '550e8400-e29b-41d4-a716-446655440000' not found",
  "error_code": "NOT_FOUND",
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "timestamp": "2025-01-05T12:00:00Z",
  "details": {
    "resource": "Item",
    "id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**409 Conflict:**
```json
{
  "detail": "Item with name='Widget' already exists",
  "error_code": "CONFLICT",
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "timestamp": "2025-01-05T12:00:00Z",
  "details": {
    "resource": "Item",
    "field": "name",
    "value": "Widget"
  }
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "String should have at least 1 character",
      "type": "string_too_short"
    }
  ],
  "error_code": "VALIDATION_ERROR",
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "timestamp": "2025-01-05T12:00:00Z"
}
```
