---
name: fastapi-entity
description: Create a new entity with model, schemas, repository, service, router, dependencies, and filters
---

# FastAPI Entity Creation

## Overview

This skill covers creating a complete entity with all necessary files following the entity-based folder structure. Each entity is self-contained with its own model, schemas, repository, service, router, dependencies, and filters.

## Entity Folder Structure

For an entity named `items`:

```
src/app/items/
├── __init__.py
├── models.py          # SQLAlchemy model
├── schemas.py         # Pydantic schemas
├── repository.py      # Data access layer
├── service.py         # Business logic layer
├── router.py          # API endpoints
├── dependencies.py    # FastAPI dependencies
└── filters.py         # fastapi-filter definitions
```

## Step 1: Create __init__.py

Create `src/app/{entity}/__init__.py`:

```python
from app.items.models import Item
from app.items.repository import ItemRepository
from app.items.router import router
from app.items.schemas import ItemCreate, ItemResponse, ItemUpdate
from app.items.service import ItemService

__all__ = [
    "Item",
    "ItemCreate",
    "ItemUpdate",
    "ItemResponse",
    "ItemRepository",
    "ItemService",
    "router",
]
```

## Step 2: Create models.py

Create `src/app/{entity}/models.py`:

```python
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


class Item(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """
    Item model.
    
    Attributes:
        id: UUID primary key
        name: Item name (required)
        description: Item description (optional)
        created_at: Creation timestamp
        updated_at: Last update timestamp
        deleted_at: Soft delete timestamp
    """

    __tablename__ = "items"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
```

## Step 3: Create schemas.py

Create `src/app/{entity}/schemas.py`:

```python
from pydantic import Field

from app.core.schemas import (
    BaseCreateSchema,
    BaseResponseSchema,
    BaseResponseWithDeletedSchema,
    BaseUpdateSchema,
)


class ItemCreate(BaseCreateSchema):
    """Schema for creating an item."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Item name",
        examples=["My Item"],
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
        description="Item description",
        examples=["A detailed description of the item"],
    )


class ItemUpdate(BaseUpdateSchema):
    """Schema for updating an item. All fields optional for PATCH."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Item name",
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
        description="Item description",
    )


class ItemResponse(BaseResponseSchema):
    """Schema for item responses."""

    name: str
    description: str | None


class ItemResponseWithDeleted(BaseResponseWithDeletedSchema):
    """Schema for item responses including soft delete info."""

    name: str
    description: str | None
```

## Step 4: Create repository.py

Create `src/app/{entity}/repository.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.postgres_repository import PostgresRepository
from app.items.models import Item
from app.items.schemas import ItemCreate, ItemUpdate


class ItemRepository(PostgresRepository[Item, ItemCreate, ItemUpdate]):
    """
    Repository for Item entity.
    
    Inherits all CRUD, pagination, filtering, bulk operations,
    and soft delete methods from PostgresRepository.
    
    Add entity-specific query methods here.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session, Item)

    async def get_by_name(self, name: str) -> Item | None:
        """
        Get item by name.
        
        Args:
            name: Item name to search for
            
        Returns:
            Item if found, None otherwise
        """
        return await self.get_by_field("name", name)
```

## Step 5: Create service.py

Create `src/app/{entity}/service.py`:

```python
from uuid import UUID

from app.core.service import BaseService
from app.exceptions import ConflictError, NotFoundError
from app.items.models import Item
from app.items.repository import ItemRepository
from app.items.schemas import ItemCreate, ItemUpdate


class ItemService(BaseService[Item, ItemCreate, ItemUpdate]):
    """
    Service for Item entity.
    
    Contains business logic and validation rules.
    Delegates data access to the repository.
    """

    def __init__(self, repository: ItemRepository):
        super().__init__(repository)
        self._repository: ItemRepository = repository

    async def create(self, obj_in: ItemCreate) -> Item:
        """
        Create a new item.
        
        Validates that the name is unique before creation.
        
        Args:
            obj_in: Item creation data
            
        Returns:
            Created item
            
        Raises:
            ConflictError: If item with same name exists
        """
        existing = await self._repository.get_by_name(obj_in.name)
        if existing:
            raise ConflictError(
                resource="Item",
                field="name",
                value=obj_in.name,
            )
        return await super().create(obj_in)

    async def get_by_id_or_raise(self, id: UUID) -> Item:
        """
        Get item by ID or raise NotFoundError.
        
        Args:
            id: Item UUID
            
        Returns:
            Item instance
            
        Raises:
            NotFoundError: If item not found
        """
        item = await self.get_by_id(id)
        if not item:
            raise NotFoundError(resource="Item", id=id)
        return item

    async def update(
        self,
        id: UUID,
        obj_in: ItemUpdate,
        exclude_unset: bool = True,
    ) -> Item:
        """
        Update an item.
        
        Validates name uniqueness if name is being changed.
        
        Args:
            id: Item UUID to update
            obj_in: Update data
            exclude_unset: Only update explicitly set fields
            
        Returns:
            Updated item
            
        Raises:
            NotFoundError: If item not found
            ConflictError: If new name conflicts with existing item
        """
        # Ensure item exists
        await self.get_by_id_or_raise(id)

        # Check name uniqueness if being updated
        if obj_in.name is not None:
            existing = await self._repository.get_by_name(obj_in.name)
            if existing and existing.id != id:
                raise ConflictError(
                    resource="Item",
                    field="name",
                    value=obj_in.name,
                )

        item = await super().update(id, obj_in, exclude_unset)
        if item is None:
            raise NotFoundError(resource="Item", id=id)
        return item

    async def delete_or_raise(self, id: UUID) -> bool:
        """
        Delete an item or raise if not found.
        
        Args:
            id: Item UUID to delete
            
        Returns:
            True if deleted
            
        Raises:
            NotFoundError: If item not found
        """
        await self.get_by_id_or_raise(id)
        return await self.delete(id)

    async def soft_delete_or_raise(self, id: UUID) -> bool:
        """
        Soft delete an item or raise if not found.
        
        Args:
            id: Item UUID to soft delete
            
        Returns:
            True if soft deleted
            
        Raises:
            NotFoundError: If item not found
        """
        await self.get_by_id_or_raise(id)
        return await self.soft_delete(id)
```

## Step 6: Create filters.py

Create `src/app/{entity}/filters.py`:

```python
from typing import Optional

from fastapi_filter.contrib.sqlalchemy import Filter

from app.items.models import Item


class ItemFilter(Filter):
    """
    Filter specification for Item queries.
    
    Supports filtering by:
    - name: Exact match
    - name__ilike: Case-insensitive partial match
    - description__ilike: Case-insensitive partial match
    
    Supports ordering by any field.
    """

    # Exact match
    name: Optional[str] = None

    # Case-insensitive contains
    name__ilike: Optional[str] = None
    description__ilike: Optional[str] = None

    # Ordering
    order_by: Optional[list[str]] = None

    class Constants(Filter.Constants):
        model = Item
        ordering_field_name = "order_by"
```

## Step 7: Create dependencies.py

Create `src/app/{entity}/dependencies.py`:

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.items.repository import ItemRepository
from app.items.service import ItemService


def get_item_repository(
    session: AsyncSession = Depends(get_db),
) -> ItemRepository:
    """
    Dependency that provides an ItemRepository instance.
    
    Args:
        session: Database session from get_db dependency
        
    Returns:
        ItemRepository instance
    """
    return ItemRepository(session)


def get_item_service(
    repository: ItemRepository = Depends(get_item_repository),
) -> ItemService:
    """
    Dependency that provides an ItemService instance.
    
    Args:
        repository: ItemRepository from get_item_repository dependency
        
    Returns:
        ItemService instance
    """
    return ItemService(repository)
```

## Step 8: Create router.py

Create `src/app/{entity}/router.py`:

```python
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi_filter import FilterDepends
from fastapi_pagination import Page, Params

from app.items.dependencies import get_item_service
from app.items.filters import ItemFilter
from app.items.models import Item
from app.items.schemas import ItemCreate, ItemResponse, ItemUpdate
from app.items.service import ItemService

router = APIRouter(prefix="/items", tags=["items"])


@router.post(
    "",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create item",
    description="Create a new item with the provided data.",
)
async def create_item(
    obj_in: ItemCreate,
    service: ItemService = Depends(get_item_service),
) -> Item:
    """Create a new item."""
    return await service.create(obj_in)


@router.get(
    "",
    response_model=Page[ItemResponse],
    summary="List items",
    description="Get a paginated list of items with optional filtering.",
)
async def list_items(
    params: Params = Depends(),
    filter_spec: ItemFilter = FilterDepends(ItemFilter),
    service: ItemService = Depends(get_item_service),
) -> Page[Item]:
    """List items with pagination and filtering."""
    return await service.get_paginated(params, filter_spec)


@router.get(
    "/{item_id}",
    response_model=ItemResponse,
    summary="Get item",
    description="Get a single item by ID.",
)
async def get_item(
    item_id: UUID,
    service: ItemService = Depends(get_item_service),
) -> Item:
    """Get item by ID."""
    return await service.get_by_id_or_raise(item_id)


@router.patch(
    "/{item_id}",
    response_model=ItemResponse,
    summary="Update item",
    description="Update an existing item. Only provided fields will be updated.",
)
async def update_item(
    item_id: UUID,
    obj_in: ItemUpdate,
    service: ItemService = Depends(get_item_service),
) -> Item:
    """Update item by ID."""
    return await service.update(item_id, obj_in)


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete item",
    description="Soft delete an item by ID.",
)
async def delete_item(
    item_id: UUID,
    service: ItemService = Depends(get_item_service),
) -> None:
    """Soft delete item by ID."""
    await service.soft_delete_or_raise(item_id)


@router.post(
    "/{item_id}/restore",
    response_model=ItemResponse,
    summary="Restore item",
    description="Restore a soft-deleted item.",
)
async def restore_item(
    item_id: UUID,
    service: ItemService = Depends(get_item_service),
) -> Item:
    """Restore a soft-deleted item."""
    await service.restore(item_id)
    return await service.get_by_id_or_raise(item_id)
```

## Step 9: Register Router

Update `src/app/api/v1/__init__.py`:

```python
from fastapi import APIRouter

from app.items.router import router as items_router

router = APIRouter()

router.include_router(items_router)
```

## Step 10: Register Model for Alembic

Update `alembic/env.py`:

```python
# Import models for autogenerate
from app.items.models import Item  # noqa: F401
```

## Step 11: Create Migration

```bash
uv run alembic revision --autogenerate -m "add items table"
uv run alembic upgrade head
```

## Generated API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/items` | Create item |
| GET | `/api/v1/items` | List items (paginated) |
| GET | `/api/v1/items/{id}` | Get item by ID |
| PATCH | `/api/v1/items/{id}` | Update item |
| DELETE | `/api/v1/items/{id}` | Soft delete item |
| POST | `/api/v1/items/{id}/restore` | Restore item |

## Query Parameters for List Endpoint

**Pagination:**
- `page`: Page number (default: 1)
- `size`: Items per page (default: 50)

**Filtering:**
- `name`: Exact name match
- `name__ilike`: Case-insensitive name contains
- `description__ilike`: Case-insensitive description contains

**Ordering:**
- `order_by`: Field to order by (prefix with `-` for descending)

**Example:**
```
GET /api/v1/items?page=1&size=20&name__ilike=widget&order_by=-created_at
```

## Adding Relationships

For entities with relationships:

```python
# models.py
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Item(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "items"
    
    name: Mapped[str] = mapped_column(String(255))
    category_id: Mapped[UUID] = mapped_column(ForeignKey("categories.id"))
    
    # Relationship
    category: Mapped["Category"] = relationship(back_populates="items")


# schemas.py
class ItemResponse(BaseResponseSchema):
    name: str
    category_id: UUID
    
class ItemWithCategoryResponse(BaseResponseSchema):
    name: str
    category: CategoryResponse  # Nested response
```
