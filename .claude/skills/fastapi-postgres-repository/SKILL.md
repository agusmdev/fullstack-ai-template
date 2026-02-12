---
name: fastapi-postgres-repository
description: Implement PostgreSQL repository with bulk upsert, soft delete filtering, and fastapi-pagination/filter integration
---

# FastAPI PostgreSQL Repository Implementation

## Overview

This skill covers the concrete PostgreSQL repository implementation with all CRUD operations, bulk upserts using ON CONFLICT, soft delete filtering, and integration with fastapi-pagination and fastapi-filter.

## Create common/postgres_repository.py

Create `src/app/common/postgres_repository.py`:

```python
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, Generic
from uuid import UUID

from fastapi_filter.contrib.sqlalchemy import Filter
from fastapi_pagination import Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import BaseModel
from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Base, SoftDeleteMixin
from app.core.repository import (
    AbstractRepository,
    CreateSchemaType,
    ModelType,
    UpdateSchemaType,
)


class PostgresRepository(
    AbstractRepository[ModelType, CreateSchemaType, UpdateSchemaType],
    Generic[ModelType, CreateSchemaType, UpdateSchemaType],
):
    """
    PostgreSQL implementation of the abstract repository.
    
    Provides full CRUD operations with:
    - Automatic soft delete filtering
    - PostgreSQL-specific bulk upsert (ON CONFLICT)
    - fastapi-pagination integration
    - fastapi-filter integration
    
    Usage:
        class ItemRepository(PostgresRepository[Item, ItemCreate, ItemUpdate]):
            pass
    """

    def __init__(self, session: AsyncSession, model: type[ModelType]):
        """
        Initialize repository with database session and model class.
        
        Args:
            session: SQLAlchemy async session
            model: SQLAlchemy model class
        """
        self._session = session
        self._model = model

    @property
    def _has_soft_delete(self) -> bool:
        """Check if model supports soft delete."""
        return issubclass(self._model, SoftDeleteMixin)

    def _base_query(self, include_deleted: bool = False):
        """
        Create base SELECT query with optional soft delete filtering.
        
        Args:
            include_deleted: If True, include soft-deleted records
            
        Returns:
            SQLAlchemy select statement
        """
        query = select(self._model)
        if self._has_soft_delete and not include_deleted:
            query = query.where(self._model.deleted_at.is_(None))
        return query

    # ==================== Basic CRUD ====================

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record."""
        data = obj_in.model_dump()
        instance = self._model(**data)
        self._session.add(instance)
        await self._session.commit()
        await self._session.refresh(instance)
        return instance

    async def get_by_id(self, id: UUID) -> ModelType | None:
        """Get a single record by ID (excludes soft-deleted)."""
        query = self._base_query().where(self._model.id == id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(self) -> Sequence[ModelType]:
        """Get all records (excludes soft-deleted)."""
        query = self._base_query()
        result = await self._session.execute(query)
        return result.scalars().all()

    async def update(
        self,
        id: UUID,
        obj_in: UpdateSchemaType,
        exclude_unset: bool = True,
    ) -> ModelType | None:
        """Update an existing record."""
        # First check if record exists
        instance = await self.get_by_id(id)
        if not instance:
            return None

        # Get update data
        if exclude_unset:
            data = obj_in.model_dump(exclude_unset=True)
        else:
            data = obj_in.model_dump()

        # Update attributes
        for field, value in data.items():
            setattr(instance, field, value)

        await self._session.commit()
        await self._session.refresh(instance)
        return instance

    async def delete(self, id: UUID) -> bool:
        """Permanently delete a record (hard delete)."""
        query = delete(self._model).where(self._model.id == id)
        result = await self._session.execute(query)
        await self._session.commit()
        return result.rowcount > 0

    # ==================== Pagination & Filtering ====================

    async def get_paginated(
        self,
        params: Params,
        filter_spec: Filter | None = None,
    ) -> AbstractPage[ModelType]:
        """Get paginated records with optional filtering."""
        query = self._base_query()

        if filter_spec is not None:
            query = filter_spec.filter(query)
            query = filter_spec.sort(query)

        return await paginate(self._session, query, params)

    async def get_filtered(
        self,
        filter_spec: Filter,
    ) -> Sequence[ModelType]:
        """Get all records matching filter criteria."""
        query = self._base_query()
        query = filter_spec.filter(query)
        query = filter_spec.sort(query)
        result = await self._session.execute(query)
        return result.scalars().all()

    async def count(self, filter_spec: Filter | None = None) -> int:
        """Count records matching optional filter."""
        query = select(func.count()).select_from(self._model)

        if self._has_soft_delete:
            query = query.where(self._model.deleted_at.is_(None))

        if filter_spec is not None:
            # Apply filter to a subquery
            subquery = self._base_query()
            subquery = filter_spec.filter(subquery)
            query = select(func.count()).select_from(subquery.subquery())

        result = await self._session.execute(query)
        return result.scalar_one()

    # ==================== Bulk Operations ====================

    async def bulk_create(
        self,
        objs_in: Sequence[CreateSchemaType],
    ) -> Sequence[ModelType]:
        """Create multiple records in a single operation."""
        if not objs_in:
            return []

        data = [obj.model_dump() for obj in objs_in]
        stmt = insert(self._model).values(data).returning(self._model)
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.scalars().all()

    async def bulk_upsert(
        self,
        objs_in: Sequence[CreateSchemaType],
        index_elements: Sequence[str],
        update_fields: Sequence[str] | None = None,
    ) -> Sequence[ModelType]:
        """
        Insert or update multiple records using PostgreSQL ON CONFLICT.
        
        Args:
            objs_in: Records to upsert
            index_elements: Columns forming the unique constraint
            update_fields: Fields to update on conflict (None = all except index)
        """
        if not objs_in:
            return []

        data = [obj.model_dump() for obj in objs_in]

        stmt = insert(self._model).values(data)

        # Determine which fields to update on conflict
        if update_fields is None:
            # Update all fields except the index elements
            update_fields = [
                key for key in data[0].keys() if key not in index_elements
            ]

        # Build the ON CONFLICT DO UPDATE clause
        update_dict = {field: getattr(stmt.excluded, field) for field in update_fields}

        # Add updated_at if model has it
        if hasattr(self._model, "updated_at"):
            update_dict["updated_at"] = func.now()

        stmt = stmt.on_conflict_do_update(
            index_elements=index_elements,
            set_=update_dict,
        ).returning(self._model)

        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.scalars().all()

    async def bulk_delete(self, ids: Sequence[UUID]) -> int:
        """Permanently delete multiple records."""
        if not ids:
            return 0

        query = delete(self._model).where(self._model.id.in_(ids))
        result = await self._session.execute(query)
        await self._session.commit()
        return result.rowcount

    # ==================== Soft Delete ====================

    async def soft_delete(self, id: UUID) -> bool:
        """Soft delete a record by setting deleted_at timestamp."""
        if not self._has_soft_delete:
            raise NotImplementedError(
                f"Model {self._model.__name__} does not support soft delete"
            )

        query = (
            update(self._model)
            .where(self._model.id == id)
            .where(self._model.deleted_at.is_(None))
            .values(deleted_at=datetime.now(UTC))
        )
        result = await self._session.execute(query)
        await self._session.commit()
        return result.rowcount > 0

    async def restore(self, id: UUID) -> bool:
        """Restore a soft-deleted record."""
        if not self._has_soft_delete:
            raise NotImplementedError(
                f"Model {self._model.__name__} does not support soft delete"
            )

        query = (
            update(self._model)
            .where(self._model.id == id)
            .where(self._model.deleted_at.is_not(None))
            .values(deleted_at=None)
        )
        result = await self._session.execute(query)
        await self._session.commit()
        return result.rowcount > 0

    async def get_by_id_with_deleted(self, id: UUID) -> ModelType | None:
        """Get a record by ID, including soft-deleted records."""
        query = self._base_query(include_deleted=True).where(self._model.id == id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_with_deleted(self) -> Sequence[ModelType]:
        """Get all records including soft-deleted ones."""
        query = self._base_query(include_deleted=True)
        result = await self._session.execute(query)
        return result.scalars().all()

    # ==================== Utility Methods ====================

    async def exists(self, id: UUID) -> bool:
        """Check if a record exists (excludes soft-deleted)."""
        query = (
            select(func.count())
            .select_from(self._model)
            .where(self._model.id == id)
        )
        if self._has_soft_delete:
            query = query.where(self._model.deleted_at.is_(None))

        result = await self._session.execute(query)
        return result.scalar_one() > 0

    async def get_by_ids(self, ids: Sequence[UUID]) -> Sequence[ModelType]:
        """Get multiple records by their IDs."""
        if not ids:
            return []

        query = self._base_query().where(self._model.id.in_(ids))
        result = await self._session.execute(query)
        return result.scalars().all()

    async def get_by_field(
        self,
        field: str,
        value: Any,
    ) -> ModelType | None:
        """Get a single record by a specific field value."""
        column = getattr(self._model, field)
        query = self._base_query().where(column == value)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_by_field(
        self,
        field: str,
        value: Any,
    ) -> Sequence[ModelType]:
        """Get all records matching a specific field value."""
        column = getattr(self._model, field)
        query = self._base_query().where(column == value)
        result = await self._session.execute(query)
        return result.scalars().all()
```

## Usage: Creating Entity Repositories

```python
# src/app/items/repository.py
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.postgres_repository import PostgresRepository
from app.items.models import Item
from app.items.schemas import ItemCreate, ItemUpdate


class ItemRepository(PostgresRepository[Item, ItemCreate, ItemUpdate]):
    """Repository for Item entity."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Item)

    # Add entity-specific methods here if needed
    async def get_by_name(self, name: str) -> Item | None:
        """Get item by name."""
        return await self.get_by_field("name", name)

    async def get_active_items(self) -> list[Item]:
        """Get all active (non-deleted) items."""
        return list(await self.get_all())
```

## Bulk Upsert Examples

### Simple Upsert (Update on Email Conflict)

```python
users = [
    UserCreate(email="user1@example.com", name="User 1"),
    UserCreate(email="user2@example.com", name="User 2"),
]

# If email exists, update name
await repo.bulk_upsert(
    users,
    index_elements=["email"],
    update_fields=["name"],
)
```

### Upsert with Composite Key

```python
# Unique constraint on (user_id, product_id)
await repo.bulk_upsert(
    cart_items,
    index_elements=["user_id", "product_id"],
    update_fields=["quantity"],
)
```

### Do Nothing on Conflict

For insert-only (skip existing), use bulk_create with error handling or create a custom method:

```python
async def bulk_create_ignore_conflicts(
    self,
    objs_in: Sequence[CreateSchemaType],
) -> Sequence[ModelType]:
    """Create records, ignoring conflicts."""
    if not objs_in:
        return []

    data = [obj.model_dump() for obj in objs_in]
    stmt = (
        insert(self._model)
        .values(data)
        .on_conflict_do_nothing()
        .returning(self._model)
    )
    result = await self._session.execute(stmt)
    await self._session.commit()
    return result.scalars().all()
```

## Performance Considerations

### Batch Size for Bulk Operations

For very large datasets, batch the operations:

```python
async def bulk_create_batched(
    self,
    objs_in: Sequence[CreateSchemaType],
    batch_size: int = 1000,
) -> int:
    """Create records in batches."""
    total = 0
    for i in range(0, len(objs_in), batch_size):
        batch = objs_in[i : i + batch_size]
        await self.bulk_create(batch)
        total += len(batch)
    return total
```

### Index Elements Must Have Index

Ensure `index_elements` columns have a unique index/constraint:

```sql
-- In migration
CREATE UNIQUE INDEX ix_users_email ON users (email);
-- Or
ALTER TABLE users ADD CONSTRAINT uq_users_email UNIQUE (email);
```

## Soft Delete Implementation Details

The soft delete filtering happens automatically in `_base_query()`:

```python
# These automatically exclude soft-deleted:
await repo.get_by_id(id)
await repo.get_all()
await repo.get_paginated(params)

# These include soft-deleted:
await repo.get_by_id_with_deleted(id)
await repo.get_all_with_deleted()
```

## Filter Integration

fastapi-filter integration works automatically:

```python
# In router
@router.get("")
async def list_items(
    filter_spec: ItemFilter = FilterDepends(ItemFilter),
    service: ItemService = Depends(get_item_service),
):
    return await service.get_paginated(params, filter_spec)

# Filter flows: Router -> Service -> Repository
# Repository calls: filter_spec.filter(query) and filter_spec.sort(query)
```
