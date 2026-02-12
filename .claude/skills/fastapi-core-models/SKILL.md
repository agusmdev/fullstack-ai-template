---
name: fastapi-core-models
description: Create SQLAlchemy base model with UUID, timestamp, and soft delete mixins for FastAPI
---

# FastAPI Core Models

## Overview

This skill covers creating the base SQLAlchemy model and reusable mixins for UUID primary keys, timestamps, and soft delete functionality.

## Create core/models.py

Create `src/app/core/models.py`:

```python
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(AsyncAttrs, DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    
    Includes AsyncAttrs for proper async lazy loading support.
    All models should inherit from this class.
    """

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """
        Generate table name from class name.
        Converts CamelCase to snake_case and pluralizes.
        
        Example: UserProfile -> user_profiles
        """
        import re
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()
        return f"{name}s"


class UUIDMixin:
    """
    Mixin that adds a UUID primary key.
    
    Uses PostgreSQL's native UUID type for optimal storage and indexing.
    Generates UUID4 by default.
    """

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        sort_order=-100,  # Ensure id appears first in table
    )


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timestamps.
    
    - created_at: Set once when record is created (server-side default)
    - updated_at: Updated automatically on every modification
    
    All timestamps are timezone-aware UTC.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        sort_order=100,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        sort_order=101,
    )


class SoftDeleteMixin:
    """
    Mixin that adds soft delete functionality.
    
    - deleted_at: NULL means not deleted, timestamp means deleted
    - Records are never physically deleted, only marked
    
    Repositories should filter out soft-deleted records by default.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        index=True,  # Index for efficient filtering
        sort_order=102,
    )

    @property
    def is_deleted(self) -> bool:
        """Check if the record is soft deleted."""
        return self.deleted_at is not None
```

## Usage Example

When creating entity models, combine the mixins:

```python
# src/app/items/models.py
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin


class Item(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Item model with UUID, timestamps, and soft delete."""
    
    __tablename__ = "items"  # Explicit table name (optional)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
```

## Generated Table Structure

The above model generates:

```sql
CREATE TABLE items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX ix_items_deleted_at ON items (deleted_at);
```

## Mixin Order Matters

Always use this order when inheriting:
```python
class MyModel(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
```

This ensures:
1. UUID `id` appears first (sort_order=-100)
2. Entity columns appear in the middle
3. Timestamps appear last (sort_order=100-102)

## Type Annotations

SQLAlchemy 2.0 uses `Mapped[]` for all column definitions:

```python
# Required field
name: Mapped[str] = mapped_column(String(255))

# Optional field
description: Mapped[str | None] = mapped_column(Text, nullable=True)

# With default
is_active: Mapped[bool] = mapped_column(default=True)

# Foreign key
user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
```

## Common Column Types

```python
from sqlalchemy import (
    String,      # VARCHAR(n)
    Text,        # TEXT (unlimited)
    Integer,     # INTEGER
    BigInteger,  # BIGINT
    Float,       # FLOAT
    Numeric,     # DECIMAL(precision, scale)
    Boolean,     # BOOLEAN
    DateTime,    # TIMESTAMP
    Date,        # DATE
    JSON,        # JSONB (PostgreSQL)
    Enum,        # ENUM type
)
from sqlalchemy.dialects.postgresql import (
    UUID,        # UUID
    ARRAY,       # ARRAY type
    JSONB,       # JSONB (explicit)
)
```

## Relationships

```python
from sqlalchemy.orm import relationship

class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"
    
    name: Mapped[str] = mapped_column(String(255))
    
    # One-to-many relationship
    items: Mapped[list["Item"]] = relationship(
        back_populates="user",
        lazy="selectin",  # Async-safe loading
    )


class Item(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "items"
    
    name: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    
    # Many-to-one relationship
    user: Mapped["User"] = relationship(back_populates="items")
```

## Async-Safe Relationship Loading

For async contexts, use these loading strategies:

| Strategy | Use Case |
|----------|----------|
| `lazy="selectin"` | Load related objects in separate SELECT |
| `lazy="joined"` | Load with JOIN (use sparingly) |
| `lazy="raise"` | Raise error if accessed (explicit loading only) |

Avoid `lazy="select"` (default) - it triggers implicit I/O in async context.

## Indexing

```python
from sqlalchemy import Index

class Item(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "items"
    
    name: Mapped[str] = mapped_column(String(255), index=True)
    status: Mapped[str] = mapped_column(String(50))
    category: Mapped[str] = mapped_column(String(100))
    
    # Composite index
    __table_args__ = (
        Index("ix_items_status_category", "status", "category"),
    )
```
