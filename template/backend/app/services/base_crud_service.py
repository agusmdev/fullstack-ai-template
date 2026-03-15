"""Module with the Base service"""

import uuid
from collections.abc import Sequence
from typing import Any, Generic

from fastapi_filter.base.filter import BaseFilterModel
from fastapi_pagination import Page, Params
from pydantic import BaseModel

from app.repositories.base_repository import BaseRepository, QueryOptions, T
from app.repositories.clauses import OnConflictClause, do_default_on_conflict


class BaseService(Generic[T]):  # noqa: UP046
    """Service to interact with entity collection.

    Args:
        repo (BaseRepository): The repository to interact with the entity collection
    """

    def __init__(self, repo: BaseRepository[T]) -> None:
        self.repo = repo

    async def get_by_id(
        self, entity_id: uuid.UUID, raise_error: bool = True
    ) -> T | None:
        return await self.repo.get(entity_id, raise_error=raise_error)

    async def get_by_field(
        self, field: str, value: Any, raise_error: bool = True
    ) -> T | None:
        return await self.repo.get_by_field(field, value, raise_error=raise_error)

    async def get_all(
        self,
        entity_filter: BaseFilterModel | None = None,
        pagination_params: Params | None = None,
        options: QueryOptions | None = None,
    ) -> list[T] | Page[T]:
        return await self.repo.get_all(entity_filter, pagination_params, options)

    async def create(self, entity: BaseModel, **extra_fields: Any) -> T:
        return await self.repo.create(entity, **extra_fields)

    async def create_many(
        self,
        entities: Sequence[BaseModel],
        on_conflict: OnConflictClause = do_default_on_conflict,
    ) -> list[T]:
        return await self.repo.create_many(entities, on_conflict=on_conflict)

    async def upsert(self, entity: BaseModel, **extra_fields: Any) -> T:
        return await self.repo.upsert(entity, **extra_fields)

    async def update(self, entity_id: uuid.UUID, entity: BaseModel) -> T:
        return await self.repo.update(entity_id, entity)

    async def delete(self, entity_id: uuid.UUID) -> None:
        return await self.repo.delete(entity_id)
