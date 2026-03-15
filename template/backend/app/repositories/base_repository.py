import abc
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, TypeVar

from fastapi_filter.base.filter import BaseFilterModel
from fastapi_pagination import Page, Params
from pydantic import BaseModel
from sqlalchemy import Selectable

from app.database.base import Base
from app.repositories.clauses import OnConflictClause, do_default_on_conflict

T = TypeVar("T", bound=Base)


@dataclass
class QueryOptions:
    """Optional modifiers for get_all queries."""

    base_query: Any | None = None
    return_scalars: bool = True
    response_model: type[BaseModel] | None = None
    pagination_kwargs: dict[str, Any] = field(default_factory=dict)


class BaseRepository[T: Base](abc.ABC):
    """Abstract base repository defining the standard CRUD interface.

    All repository implementations must provide these methods using
    direct SQL operations (INSERT, UPDATE, DELETE) with RETURNING clauses.
    """

    # READ operations
    @abc.abstractmethod
    async def get(
        self,
        entity_id: uuid.UUID,
        raise_error: bool = True,
        response_model: type[BaseModel] | None = None,
    ) -> T | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_by_field(
        self,
        field: str,
        value: Any,
        raise_error: bool = True,
        response_model: type[BaseModel] | None = None,
    ) -> T | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_all(
        self,
        entity_filter: BaseFilterModel | None = None,
        options: QueryOptions | None = None,
    ) -> list[T]:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_all_paginated(
        self,
        pagination_params: Params,
        entity_filter: BaseFilterModel | None = None,
        options: QueryOptions | None = None,
    ) -> Page[T]:
        raise NotImplementedError

    # CREATE operations
    @abc.abstractmethod
    async def create(self, entity: BaseModel, **extra_fields: Any) -> T:
        """Create a single entity using INSERT ... RETURNING."""
        raise NotImplementedError

    @abc.abstractmethod
    async def create_many(
        self,
        entities: Sequence[BaseModel],
        on_conflict: OnConflictClause = do_default_on_conflict,
    ) -> list[T]:
        """Create multiple entities using bulk INSERT ... RETURNING."""
        raise NotImplementedError

    # UPSERT operation
    @abc.abstractmethod
    async def upsert(self, entity: BaseModel, **extra_fields: Any) -> T:
        """Insert or update based on primary key using INSERT ... ON CONFLICT DO UPDATE."""
        raise NotImplementedError

    # UPDATE operation
    @abc.abstractmethod
    async def update(
        self, entity_id: uuid.UUID, updated_entity: BaseModel | dict[str, Any]
    ) -> T:
        """Update an entity using UPDATE ... RETURNING."""
        raise NotImplementedError

    # DELETE operations
    @abc.abstractmethod
    async def delete(self, entity_id: uuid.UUID) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def delete_many(self, delete_filter_query: Selectable) -> None:
        raise NotImplementedError
