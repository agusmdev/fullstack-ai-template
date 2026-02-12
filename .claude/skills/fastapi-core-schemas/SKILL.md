---
name: fastapi-core-schemas
description: Create Pydantic v2 base schemas for request validation and response serialization in FastAPI
---

# FastAPI Core Schemas

## Overview

This skill covers creating base Pydantic v2 schemas for consistent request/response handling across the application.

## Create core/schemas.py

Create `src/app/core/schemas.py`:

```python
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """
    Base schema for all Pydantic models.
    
    Configured with:
    - from_attributes: Enables ORM mode (read from SQLAlchemy models)
    - populate_by_name: Allow using field names or aliases
    - str_strip_whitespace: Strip whitespace from string fields
    - validate_default: Validate default values
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_default=True,
    )


class BaseCreateSchema(BaseSchema):
    """
    Base schema for create operations.
    
    Does NOT include id, timestamps, or deleted_at.
    Only fields that the client provides when creating a resource.
    """

    pass


class BaseUpdateSchema(BaseSchema):
    """
    Base schema for update operations.
    
    All fields should be Optional to support partial updates (PATCH).
    Does NOT include id, timestamps, or deleted_at.
    """

    pass


class BaseResponseSchema(BaseSchema):
    """
    Base schema for response serialization.
    
    Includes:
    - id: UUID primary key
    - created_at: Creation timestamp
    - updated_at: Last update timestamp
    """

    id: UUID
    created_at: datetime
    updated_at: datetime


class BaseResponseWithDeletedSchema(BaseResponseSchema):
    """
    Response schema that includes soft delete information.
    
    Use when the API needs to return deleted_at field,
    such as admin endpoints or trash/archive views.
    """

    deleted_at: datetime | None = None
```

## Usage Example

When creating entity schemas, inherit from the base schemas:

```python
# src/app/items/schemas.py
from uuid import UUID

from pydantic import Field

from app.core.schemas import (
    BaseCreateSchema,
    BaseUpdateSchema,
    BaseResponseSchema,
)


class ItemCreate(BaseCreateSchema):
    """Schema for creating an item."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    category_id: UUID


class ItemUpdate(BaseUpdateSchema):
    """Schema for updating an item. All fields optional for PATCH."""
    
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    category_id: UUID | None = None


class ItemResponse(BaseResponseSchema):
    """Schema for item responses."""
    
    name: str
    description: str | None
    category_id: UUID
```

## Pydantic v2 Configuration Options

| Option | Purpose | Default |
|--------|---------|---------|
| `from_attributes` | Read data from ORM model attributes | `False` |
| `populate_by_name` | Allow field name or alias | `False` |
| `str_strip_whitespace` | Strip whitespace from strings | `False` |
| `validate_default` | Validate default values | `False` |
| `strict` | Strict type coercion | `False` |
| `extra` | Handle extra fields: `"ignore"`, `"forbid"`, `"allow"` | `"ignore"` |

## Field Validation

```python
from pydantic import Field, field_validator, model_validator


class ItemCreate(BaseCreateSchema):
    name: str = Field(
        ...,  # Required
        min_length=1,
        max_length=255,
        description="Item name",
        examples=["My Item"],
    )
    price: float = Field(
        ...,
        gt=0,  # Greater than 0
        le=1000000,  # Less than or equal to
        description="Item price in USD",
    )
    tags: list[str] = Field(
        default_factory=list,
        max_length=10,  # Max 10 tags
    )
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Custom name validation."""
        if v.lower() == "test":
            raise ValueError("Name cannot be 'test'")
        return v.title()
    
    @model_validator(mode="after")
    def validate_model(self) -> "ItemCreate":
        """Cross-field validation."""
        if self.price > 100 and not self.tags:
            raise ValueError("Expensive items must have tags")
        return self
```

## Nested Schemas

```python
class CategoryResponse(BaseResponseSchema):
    name: str


class ItemWithCategoryResponse(BaseResponseSchema):
    """Item response with nested category."""
    
    name: str
    description: str | None
    category: CategoryResponse  # Nested schema
```

## List Response Pattern

For list endpoints with metadata:

```python
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ListResponse(BaseModel, Generic[T]):
    """Generic list response with metadata."""
    
    items: list[T]
    total: int
    
    model_config = ConfigDict(from_attributes=True)


# Usage:
# ListResponse[ItemResponse]
```

## Integration with fastapi-pagination

When using fastapi-pagination, you don't need custom list schemas. The library provides `Page[T]`:

```python
from fastapi_pagination import Page

# Router returns:
# Page[ItemResponse]

# Which produces:
# {
#   "items": [...],
#   "total": 100,
#   "page": 1,
#   "size": 50,
#   "pages": 2
# }
```

## Computed Fields (Pydantic v2)

```python
from pydantic import computed_field


class ItemResponse(BaseResponseSchema):
    name: str
    price: float
    quantity: int
    
    @computed_field
    @property
    def total_value(self) -> float:
        """Computed field for total value."""
        return self.price * self.quantity
```

## Serialization Aliases

```python
from pydantic import Field


class ItemResponse(BaseResponseSchema):
    internal_id: str = Field(serialization_alias="id")
    item_name: str = Field(serialization_alias="name")
```

## Excluding Fields from Response

```python
class UserResponse(BaseResponseSchema):
    username: str
    email: str
    password_hash: str = Field(exclude=True)  # Never serialized
```

## Schema for Query Parameters

```python
from pydantic import BaseModel, Field


class ItemQueryParams(BaseModel):
    """Query parameters for listing items."""
    
    search: str | None = Field(default=None, min_length=1, max_length=100)
    category_id: UUID | None = None
    min_price: float | None = Field(default=None, ge=0)
    max_price: float | None = Field(default=None, ge=0)
    is_active: bool = True
    
    model_config = ConfigDict(extra="forbid")  # Reject unknown params
```
