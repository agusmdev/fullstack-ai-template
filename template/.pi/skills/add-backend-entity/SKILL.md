---
name: add-backend-entity
description: Step-by-step guide to add a new entity/module to the FastAPI backend. Covers model, schema, repository, service, router, filters, dependencies, and registration. Use when creating new API resources or backend modules.
---

# Add Backend Entity

Complete guide for adding a new entity module to `app/modules/`. The `items` module is the canonical reference — mirror its structure.

## Step 1: Model (`models.py`)

```python
"""YourEntity model."""

import uuid

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import TimestampMixin


class YourEntity(TimestampMixin, Base):
    __tablename__ = "your_entity"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    # Add fields as needed. Use Mapped[] + mapped_column() for all columns.
```

**Available mixins** (`app/database/mixins.py`):
- `TimestampMixin` — adds `created_at` / `updated_at` with UTC timestamps and indexes
- `JSONUpdatesMixing` — adds `updates_metadata` JSONB column

**Conventions:**
- UUID primary keys via `uuid.uuid4`
- Use `Mapped[type]` + `mapped_column()` (SQLAlchemy 2 style)
- Use `StrEnum` from `app/database/mixins.py` for enum fields

## Step 2: Schemas (`schemas.py`)

```python
"""YourEntity schemas — request and response models."""

import uuid

from pydantic import BaseModel, Field

from app.core.optional_model import partial_model
from app.database.mixins import OrmBaseModel


class YourEntityBase(BaseModel):
    """Base schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=5000)


class YourEntityCreate(YourEntityBase):
    """Schema for creating."""
    pass


@partial_model
class YourEntityUpdate(YourEntityBase):
    """Schema for updating (all fields become optional via @partial_model)."""
    pass


class YourEntityResponse(YourEntityBase, OrmBaseModel):
    """Response schema (includes id + timestamps from OrmBaseModel)."""
    id: uuid.UUID
```

**Key patterns:**
- `@partial_model` — makes all fields optional for PATCH/update operations
- `OrmBaseModel` — Pydantic `BaseModel` with `from_attributes=True` for SQLAlchemy compatibility
- Separate Create/Update/Response schemas

## Step 3: Repository (`repository.py`)

```python
"""YourEntity repository — database access layer."""

from app.modules.your_entity.models import YourEntity
from app.repositories.sql_repository import SQLAlchemyRepository


class YourEntityRepository(SQLAlchemyRepository[YourEntity]):
    """Repository for YourEntity.

    Inherits CRUD: get, get_all, create, create_many, upsert, update, delete, delete_many
    """
    model = YourEntity
```

Only add custom methods if you need queries beyond standard CRUD. The base `SQLAlchemyRepository` provides:
- `get(entity_id, raise_error=True, filter_field="id")` — single entity lookup
- `get_all(filter, pagination)` — list with filtering and pagination
- `create(entity, **extra_fields)` — INSERT...RETURNING
- `create_many(entities, on_conflict)` — bulk INSERT
- `upsert(entity)` — INSERT...ON CONFLICT DO UPDATE
- `update(entity_id, entity)` — UPDATE...RETURNING
- `delete(entity_id)` / `delete_many(filter_query)` — DELETE

## Step 4: Service (`service.py`)

```python
"""YourEntity service — business logic layer."""

from app.modules.your_entity.models import YourEntity
from app.modules.your_entity.repository import YourEntityRepository
from app.services.base_crud_service import BaseService


class YourEntityService(BaseService[YourEntity]):
    """Service for YourEntity.

    Inherits: get_by_id, get_all, create, create_many, upsert, update, delete
    """
    def __init__(self, repo: YourEntityRepository) -> None:
        self.repo = repo

    # Add business logic methods here. Example:
    # async def get_by_name(self, name: str) -> YourEntity:
    #     entity = await self.repo.get(name, filter_field="name", raise_error=False)
    #     if not entity:
    #         raise NotFoundError(detail=f"Entity with name '{name}' not found")
    #     return entity
```

## Step 5: Filters (`filters.py`)

```python
"""YourEntity filters — for filtering and searching."""

from fastapi_filter.contrib.sqlalchemy.filter import Filter

from app.modules.your_entity.models import YourEntity


class YourEntityFilter(Filter):
    """Filter for YourEntity queries.

    Usage in requests: ?search=keyword, ?name__like=pattern
    """
    search: str | None = None

    class Constants(Filter.Constants):
        model = YourEntity
        search_model_fields = ["name", "description"]  # Fields for ?search=
```

**Available operators** (via query params): `__eq`, `__neq`, `__gt`, `__gte`, `__lt`, `__lte`, `__like`, `__ilike`, `__in`, `__not_in`, `__isnull`

For join-based filtering, use `JoinFilter` from `app/core/advanced_filtering.py`.

## Step 6: Dependencies (`dependencies.py`)

```python
"""Dependency factory functions for YourEntity module."""

from fastapi import Depends

from app.dependencies import get_repository
from app.modules.your_entity.repository import YourEntityRepository
from app.modules.your_entity.service import YourEntityService


def get_your_entity_service(
    repo: YourEntityRepository = Depends(get_repository(YourEntityRepository)),
) -> YourEntityService:
    return YourEntityService(repo=repo)
```

## Step 7: Router (`routers.py`)

```python
"""YourEntity router — CRUD endpoints."""

import uuid
from typing import TYPE_CHECKING, cast

from fastapi import APIRouter, Body, Depends, status
from fastapi_pagination import Page, Params

from app.core.logging import log_action, log_entity
from app.core.permissions.auth import AuthenticatedUser
from app.modules.your_entity.dependencies import get_your_entity_service
from app.modules.your_entity.filters import YourEntityFilter
from app.modules.your_entity.schemas import YourEntityCreate, YourEntityResponse, YourEntityUpdate
from app.modules.your_entity.service import YourEntityService

if TYPE_CHECKING:
    from app.modules.your_entity.models import YourEntity

your_entity_router = APIRouter(
    prefix="/your-entities",
    tags=["your-entities"],
    dependencies=[Depends(AuthenticatedUser.current_user_id)],  # Protected
)


@your_entity_router.get("", status_code=status.HTTP_200_OK)
async def list_entities(
    pagination: Params = Depends(),
    entity_filter: YourEntityFilter = Depends(),
    service: YourEntityService = Depends(get_your_entity_service),
) -> Page[YourEntityResponse]:
    log_action("list")
    result = await service.get_all(entity_filter=entity_filter, pagination_params=pagination)
    return cast("Page[YourEntityResponse]", result)


@your_entity_router.get("/{entity_id}", status_code=status.HTTP_200_OK)
async def get_entity(
    entity_id: uuid.UUID,
    service: YourEntityService = Depends(get_your_entity_service),
) -> YourEntityResponse:
    log_action("get")
    log_entity("your_entity", entity_id)
    result = await service.get_by_id(entity_id)
    return cast("YourEntityResponse", result)


@your_entity_router.post("", status_code=status.HTTP_201_CREATED)
async def create_entity(
    entity: YourEntityCreate = Body(...),
    service: YourEntityService = Depends(get_your_entity_service),
) -> YourEntityResponse:
    log_action("create")
    result = await service.create(entity)
    log_entity("your_entity", result.id)
    return cast("YourEntityResponse", result)


@your_entity_router.patch("/{entity_id}", status_code=status.HTTP_200_OK)
async def update_entity(
    entity_id: uuid.UUID,
    entity: YourEntityUpdate = Body(...),
    service: YourEntityService = Depends(get_your_entity_service),
) -> YourEntityResponse:
    log_action("update")
    log_entity("your_entity", entity_id)
    return cast("YourEntityResponse", await service.update(entity_id, entity))


@your_entity_router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entity(
    entity_id: uuid.UUID,
    service: YourEntityService = Depends(get_your_entity_service),
) -> None:
    log_action("delete")
    log_entity("your_entity", entity_id)
    await service.delete(entity_id)
```

## Step 8: Register the Router

In `app/routers.py`, import and include:

```python
from app.modules.your_entity.routers import your_entity_router

def get_app_router() -> APIRouter:
    router = APIRouter()
    # ... existing routers ...
    router.include_router(your_entity_router)
    return router
```

## Step 9: Generate Migration

```bash
uv run alembic revision --autogenerate -m "add your_entity table"
uv run alembic upgrade head
```

**Review the generated migration** — autogenerate is not perfect. Check:
- Table name matches `__tablename__`
- All columns are present with correct types
- Indexes and unique constraints are included
- Enum types are handled (uses `alembic_postgresql_enum`)

## Checklist

- [ ] `models.py` — SQLAlchemy model with `Base` + `TimestampMixin`
- [ ] `schemas.py` — Create, Update (`@partial_model`), Response schemas
- [ ] `repository.py` — Inherits `SQLAlchemyRepository[YourModel]`
- [ ] `service.py` — Inherits `BaseService[YourModel]`, custom business logic
- [ ] `filters.py` — Filter class with `search_model_fields`
- [ ] `dependencies.py` — `get_*_service()` factory using `Depends(get_repository(...))`
- [ ] `routers.py` — CRUD endpoints with auth, logging, pagination
- [ ] Registered in `app/routers.py`
- [ ] Migration generated and reviewed
- [ ] Tests written
