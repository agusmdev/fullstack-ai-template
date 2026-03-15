import abc
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Literal, TypeVar, overload

from fastapi_filter.base.filter import BaseFilterModel
from fastapi_pagination import Page, Params
from pydantic import BaseModel
from sqlalchemy import Select, Selectable

from app.database.base import Base
from app.repositories.clauses import OnConflictClause, do_default_on_conflict

T = TypeVar("T", bound=Base)


@dataclass
class QueryOptions:
    """Optional modifiers for get_all queries.

    Attributes:
        base_query: Optional SQLAlchemy Select statement to use as the query base.
            When provided, the repository will use this as the starting point instead
            of building a default SELECT from the model.
        return_scalars: Whether to return scalar row objects (True) or full Row tuples.
        response_model: Optional Pydantic model to map results into.
        pagination_kwargs: Extra keyword arguments forwarded to fastapi_pagination.paginate().
            Accepted keys include: ``unique`` (bool), ``transformer`` (callable).
    """

    base_query: Select[Any] | None = None
    return_scalars: bool = True
    response_model: type[BaseModel] | None = None
    pagination_kwargs: dict[str, Any] = field(default_factory=dict)


class BaseRepository[T: Base](abc.ABC):
    """Abstract base repository defining the standard CRUD interface.

    All repository implementations must provide these methods using
    direct SQL operations (INSERT, UPDATE, DELETE) with RETURNING clauses.
    """

    # READ operations
    @overload
    async def get(
        self,
        entity_id: uuid.UUID,
        raise_error: Literal[True],
        response_model: type[BaseModel] | None = None,
    ) -> T: ...

    @overload
    async def get(
        self,
        entity_id: uuid.UUID,
        raise_error: Literal[False],
        response_model: type[BaseModel] | None = None,
    ) -> T | None: ...

    @abc.abstractmethod
    async def get(
        self,
        entity_id: uuid.UUID,
        raise_error: bool = True,
        response_model: type[BaseModel] | None = None,
    ) -> T | None:
        raise NotImplementedError

    @overload
    async def get_by_field(
        self,
        field: str,
        value: Any,
        raise_error: Literal[True],
        response_model: type[BaseModel] | None = None,
    ) -> T: ...

    @overload
    async def get_by_field(
        self,
        field: str,
        value: Any,
        raise_error: Literal[False],
        response_model: type[BaseModel] | None = None,
    ) -> T | None: ...

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
