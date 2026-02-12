---
name: fastapi-core-service
description: Create base service class that wraps repository operations and provides business logic hooks
---

# FastAPI Core Service

## Overview

This skill covers creating the base service class that acts as an intermediary between routers and repositories. Services contain business logic and orchestrate repository calls.

## Create core/service.py

Create `src/app/core/service.py`:

```python
from collections.abc import Sequence
from typing import Generic
from uuid import UUID

from fastapi_filter.contrib.sqlalchemy import Filter
from fastapi_pagination import Params
from fastapi_pagination.bases import AbstractPage

from app.core.repository import (
    AbstractRepository,
    CreateSchemaType,
    ModelType,
    UpdateSchemaType,
)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base service class providing standard CRUD operations.
    
    Services:
    - Wrap repository operations
    - Contain business logic
    - Orchestrate multiple repository calls
    - Handle cross-cutting concerns (logging, events, etc.)
    
    Services should NOT:
    - Write SQL queries (delegate to repository)
    - Handle HTTP concerns (that's the router's job)
    - Access the database session directly
    
    Type Parameters:
        ModelType: SQLAlchemy model class
        CreateSchemaType: Pydantic schema for create operations
        UpdateSchemaType: Pydantic schema for update operations
    
    Usage:
        class ItemService(BaseService[Item, ItemCreate, ItemUpdate]):
            pass
    """

    def __init__(
        self,
        repository: AbstractRepository[ModelType, CreateSchemaType, UpdateSchemaType],
    ):
        """
        Initialize service with repository.
        
        Args:
            repository: Repository instance for data access
        """
        self._repository = repository

    # ==================== Basic CRUD ====================

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record.
        
        Override to add business logic before/after creation.
        
        Args:
            obj_in: Creation data
            
        Returns:
            Created model instance
        """
        return await self._repository.create(obj_in)

    async def get_by_id(self, id: UUID) -> ModelType | None:
        """
        Get a single record by ID.
        
        Args:
            id: UUID of the record
            
        Returns:
            Model instance if found, None otherwise
        """
        return await self._repository.get_by_id(id)

    async def get_all(self) -> Sequence[ModelType]:
        """
        Get all records.
        
        Returns:
            Sequence of model instances
        """
        return await self._repository.get_all()

    async def update(
        self,
        id: UUID,
        obj_in: UpdateSchemaType,
        exclude_unset: bool = True,
    ) -> ModelType | None:
        """
        Update an existing record.
        
        Override to add business logic before/after update.
        
        Args:
            id: UUID of record to update
            obj_in: Update data
            exclude_unset: Only update explicitly set fields
            
        Returns:
            Updated model instance if found, None otherwise
        """
        return await self._repository.update(id, obj_in, exclude_unset)

    async def delete(self, id: UUID) -> bool:
        """
        Permanently delete a record.
        
        Args:
            id: UUID of record to delete
            
        Returns:
            True if deleted, False if not found
        """
        return await self._repository.delete(id)

    # ==================== Pagination & Filtering ====================

    async def get_paginated(
        self,
        params: Params,
        filter_spec: Filter | None = None,
    ) -> AbstractPage[ModelType]:
        """
        Get paginated records with optional filtering.
        
        This method receives the filter from the router layer and
        passes it to the repository.
        
        Args:
            params: Pagination parameters
            filter_spec: Optional filter specification
            
        Returns:
            Paginated result
        """
        return await self._repository.get_paginated(params, filter_spec)

    async def get_filtered(
        self,
        filter_spec: Filter,
    ) -> Sequence[ModelType]:
        """
        Get all records matching filter.
        
        Args:
            filter_spec: Filter specification
            
        Returns:
            Matching records
        """
        return await self._repository.get_filtered(filter_spec)

    async def count(self, filter_spec: Filter | None = None) -> int:
        """
        Count records.
        
        Args:
            filter_spec: Optional filter specification
            
        Returns:
            Number of matching records
        """
        return await self._repository.count(filter_spec)

    # ==================== Bulk Operations ====================

    async def bulk_create(
        self,
        objs_in: Sequence[CreateSchemaType],
    ) -> Sequence[ModelType]:
        """
        Create multiple records.
        
        Args:
            objs_in: Sequence of creation data
            
        Returns:
            Created model instances
        """
        return await self._repository.bulk_create(objs_in)

    async def bulk_upsert(
        self,
        objs_in: Sequence[CreateSchemaType],
        index_elements: Sequence[str],
        update_fields: Sequence[str] | None = None,
    ) -> Sequence[ModelType]:
        """
        Upsert multiple records.
        
        Args:
            objs_in: Records to upsert
            index_elements: Unique constraint columns
            update_fields: Fields to update on conflict
            
        Returns:
            Upserted model instances
        """
        return await self._repository.bulk_upsert(
            objs_in, index_elements, update_fields
        )

    async def bulk_delete(self, ids: Sequence[UUID]) -> int:
        """
        Delete multiple records.
        
        Args:
            ids: UUIDs to delete
            
        Returns:
            Number deleted
        """
        return await self._repository.bulk_delete(ids)

    # ==================== Soft Delete ====================

    async def soft_delete(self, id: UUID) -> bool:
        """
        Soft delete a record.
        
        Args:
            id: UUID of record
            
        Returns:
            True if soft deleted
        """
        return await self._repository.soft_delete(id)

    async def restore(self, id: UUID) -> bool:
        """
        Restore a soft-deleted record.
        
        Args:
            id: UUID of record
            
        Returns:
            True if restored
        """
        return await self._repository.restore(id)

    async def get_by_id_with_deleted(self, id: UUID) -> ModelType | None:
        """
        Get record including soft-deleted.
        
        Args:
            id: UUID of record
            
        Returns:
            Model instance if found
        """
        return await self._repository.get_by_id_with_deleted(id)

    # ==================== Utility ====================

    async def exists(self, id: UUID) -> bool:
        """
        Check if record exists.
        
        Args:
            id: UUID to check
            
        Returns:
            True if exists
        """
        return await self._repository.exists(id)

    async def get_by_ids(self, ids: Sequence[UUID]) -> Sequence[ModelType]:
        """
        Get multiple records by IDs.
        
        Args:
            ids: UUIDs to fetch
            
        Returns:
            Found model instances
        """
        return await self._repository.get_by_ids(ids)
```

## Usage: Creating Entity Services

```python
# src/app/items/service.py
from uuid import UUID

from app.core.service import BaseService
from app.exceptions import ConflictError, NotFoundError
from app.items.models import Item
from app.items.repository import ItemRepository
from app.items.schemas import ItemCreate, ItemUpdate


class ItemService(BaseService[Item, ItemCreate, ItemUpdate]):
    """Service for Item entity with business logic."""

    def __init__(self, repository: ItemRepository):
        super().__init__(repository)
        # Type hint for IDE support
        self._repository: ItemRepository = repository

    async def create(self, obj_in: ItemCreate) -> Item:
        """
        Create item with duplicate name check.
        
        Raises:
            ConflictError: If item with same name exists
        """
        # Business logic: check for duplicate name
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
        
        Useful when you need to ensure the item exists.
        
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
    ) -> Item | None:
        """
        Update item with duplicate name check.
        
        Raises:
            ConflictError: If new name conflicts with existing item
        """
        # Business logic: check name uniqueness on update
        if obj_in.name is not None:
            existing = await self._repository.get_by_name(obj_in.name)
            if existing and existing.id != id:
                raise ConflictError(
                    resource="Item",
                    field="name",
                    value=obj_in.name,
                )

        return await super().update(id, obj_in, exclude_unset)
```

## Service Patterns

### 1. Get or Raise Pattern

```python
async def get_by_id_or_raise(self, id: UUID) -> ModelType:
    """Get record or raise NotFoundError."""
    instance = await self.get_by_id(id)
    if not instance:
        raise NotFoundError(resource=self._model_name, id=id)
    return instance
```

### 2. Validation Before Create

```python
async def create(self, obj_in: CreateSchemaType) -> ModelType:
    """Create with pre-validation."""
    await self._validate_create(obj_in)
    return await super().create(obj_in)

async def _validate_create(self, obj_in: CreateSchemaType) -> None:
    """Override in subclass to add validation logic."""
    pass
```

### 3. Multi-Repository Orchestration

```python
class OrderService(BaseService[Order, OrderCreate, OrderUpdate]):
    def __init__(
        self,
        repository: OrderRepository,
        item_repository: ItemRepository,
        user_repository: UserRepository,
    ):
        super().__init__(repository)
        self._item_repo = item_repository
        self._user_repo = user_repository

    async def create(self, obj_in: OrderCreate) -> Order:
        # Validate user exists
        user = await self._user_repo.get_by_id(obj_in.user_id)
        if not user:
            raise NotFoundError(resource="User", id=obj_in.user_id)

        # Validate all items exist
        items = await self._item_repo.get_by_ids(obj_in.item_ids)
        if len(items) != len(obj_in.item_ids):
            raise ValidationError("Some items not found")

        return await super().create(obj_in)
```

### 4. Events/Hooks Pattern

```python
class ItemService(BaseService[Item, ItemCreate, ItemUpdate]):
    async def create(self, obj_in: ItemCreate) -> Item:
        item = await super().create(obj_in)
        await self._on_created(item)
        return item

    async def _on_created(self, item: Item) -> None:
        """Hook called after item creation."""
        # Send notification, update cache, emit event, etc.
        logger.info(f"Item created: {item.id}")
```

### 5. Transaction Boundaries

By default, each repository method commits its transaction. For complex operations spanning multiple writes, consider transaction management:

```python
# In repository, add a method that doesn't commit:
async def create_no_commit(self, obj_in: CreateSchemaType) -> ModelType:
    data = obj_in.model_dump()
    instance = self._model(**data)
    self._session.add(instance)
    await self._session.flush()  # Get ID without commit
    return instance

# In service:
async def create_order_with_items(self, order: OrderCreate) -> Order:
    async with self._session.begin():  # Transaction
        order = await self._order_repo.create_no_commit(order)
        for item in order.items:
            await self._order_item_repo.create_no_commit(item)
    # Commits on exit
    return order
```

## Key Principles

1. **Services contain business logic** - validation, orchestration, rules
2. **Services delegate data access** - never write SQL in services
3. **Services are stateless** - no instance state between calls
4. **Services raise domain exceptions** - NotFoundError, ConflictError, etc.
5. **Services are testable** - mock the repository for unit tests
