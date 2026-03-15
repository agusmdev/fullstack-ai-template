"""Module with the Base service"""

import uuid
from collections.abc import Sequence
from typing import Any, Generic

from fastapi_filter.base.filter import BaseFilterModel
from fastapi_pagination import Page, Params
from pydantic import BaseModel

from app.core.logging import log_entity
from app.repositories.base_repository import BaseRepository, QueryOptions, T
from app.repositories.clauses import OnConflictClause, do_default_on_conflict


class BaseService(Generic[T]):  # noqa: UP046
    """Service base class providing CRUD operations with automatic entity context logging.

    Wraps a repository and adds cross-cutting policy: every mutating operation
    (create, upsert, update, delete) and successful single-entity reads automatically
    record the entity type and ID in the current wide-event log context. This gives
    structured observability at the service layer without requiring routers or domain
    services to instrument individual operations.

    Domain services should subclass this and add business logic (validation, domain
    events, authorization checks) on top of the inherited methods.

    Args:
        repo: The repository to delegate persistence operations to.
    """

    def __init__(self, repo: BaseRepository[T]) -> None:
        self.repo = repo

    def _entity_type(self) -> str:
        """Return the display name for the entity managed by this service."""
        model = getattr(self.repo, "model", None)
        if model is not None and hasattr(model, "_display_name"):
            return model._display_name()
        return type(self).__name__.removesuffix("Service")

    def _log_entity(self, entity_id: Any) -> None:
        """Record entity type and ID in the wide-event context."""
        log_entity(self._entity_type(), entity_id)

    async def get_by_id(
        self, entity_id: uuid.UUID, raise_error: bool = True
    ) -> T | None:
        result = await self.repo.get(entity_id, raise_error=raise_error)
        if result is not None:
            self._log_entity(entity_id)
        return result

    async def get_by_field(
        self, field: str, value: Any, raise_error: bool = True
    ) -> T | None:
        result = await self.repo.get_by_field(field, value, raise_error=raise_error)
        if result is not None:
            if entity_id := getattr(result, "id", None):
                self._log_entity(entity_id)
        return result

    async def get_all(
        self,
        entity_filter: BaseFilterModel | None = None,
        options: QueryOptions | None = None,
    ) -> list[T]:
        return await self.repo.get_all(entity_filter, options)

    async def get_all_paginated(
        self,
        pagination_params: Params,
        entity_filter: BaseFilterModel | None = None,
        options: QueryOptions | None = None,
    ) -> Page[T]:
        return await self.repo.get_all_paginated(pagination_params, entity_filter, options)

    async def create(self, entity: BaseModel, **extra_fields: Any) -> T:
        result = await self.repo.create(entity, **extra_fields)
        if entity_id := getattr(result, "id", None):
            self._log_entity(entity_id)
        return result

    async def create_many(
        self,
        entities: Sequence[BaseModel],
        on_conflict: OnConflictClause = do_default_on_conflict,
    ) -> list[T]:
        results = await self.repo.create_many(entities, on_conflict=on_conflict)
        for result in results:
            if entity_id := getattr(result, "id", None):
                self._log_entity(entity_id)
        return results

    async def upsert(self, entity: BaseModel, **extra_fields: Any) -> T:
        result = await self.repo.upsert(entity, **extra_fields)
        if entity_id := getattr(result, "id", None):
            self._log_entity(entity_id)
        return result

    async def update(self, entity_id: uuid.UUID, entity: BaseModel) -> T:
        result = await self.repo.update(entity_id, entity)
        self._log_entity(entity_id)
        return result

    async def delete(self, entity_id: uuid.UUID) -> None:
        await self.repo.delete(entity_id)
        self._log_entity(entity_id)
