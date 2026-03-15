from loguru import logger
import uuid
from collections.abc import Callable, Sequence
from functools import wraps
from typing import Any, TypeVar

from fastapi_filter.base.filter import BaseFilterModel
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import BaseModel
from sqlalchemy import Selectable, delete, select
from sqlalchemy import update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.repositories.base_repository import BaseRepository, T
from app.repositories.clauses import (
    OnConflictClause,
    do_default_on_conflict,
)
from app.repositories.exceptions import DuplicateError, NotFoundError, ReferencedError
from app.repositories.query_builder import QueryBuilder

F = TypeVar("F", bound=Callable[..., Any])


class SQLAlchemyRepository(BaseRepository[T]):
    """SQLAlchemy repository with extensible database-specific behavior.

    This repository provides CRUD operations with PostgreSQL-specific features.
    Subclasses can override protected methods to adapt to different databases.
    """

    model: type[T]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._query_builder = QueryBuilder(self.model)

    def _generate_select_from_pydantic(
        self, pydantic_model: type[BaseModel], query: Selectable | None = None
    ) -> Select[Any]:
        return self._query_builder.build_select_from_pydantic(pydantic_model, query)

    def _base_query(self, **kwargs: Any) -> Select[Any]:
        return select(self.model)

    def _normalize_values(
        self,
        entity: BaseModel | dict[str, Any],
        exclude_unset: bool = False,
        **extra_fields: Any,
    ) -> dict[str, Any]:
        """Normalize entity to dict values for SQL operations."""
        if isinstance(entity, dict):
            values = entity
        elif exclude_unset:
            values = entity.model_dump(exclude_unset=True)
        else:
            values = entity.model_dump()

        return {**values, **extra_fields} if extra_fields else values

    @staticmethod
    def _get_insert_dialect() -> Any:
        """Get the database-specific insert statement.

        Override this for different database backends.

        Returns:
            The dialect-specific insert function (e.g., PostgreSQL's insert)
        """
        from sqlalchemy.dialects.postgresql import insert

        return insert

    @classmethod
    def _parse_integrity_error(cls, error: Exception) -> Exception:
        """Parse database-specific integrity errors.

        Override this for different database backends.

        Args:
            error: The original integrity error

        Returns:
            A RepositoryError subclass if recognized, otherwise the original error unchanged.
            The caller (handle_commit_errors) is responsible for re-raising unparsed errors.
        """
        import sqlalchemy.exc as sqlalchemy_exc

        if isinstance(error, sqlalchemy_exc.IntegrityError):
            error_msg = str(error.orig).lower() if error.orig else ""
            if "unique violation" in error_msg or "duplicate key" in error_msg:
                return DuplicateError(
                    detail=f"Duplicate entry found in {cls.model._display_name()}"
                )
            if (
                "foreign key violation" in error_msg
                or "is still referenced" in error_msg
            ):
                return ReferencedError(
                    detail=f"{cls.model._display_name()} is being referenced by another table"
                )
        return error

    @staticmethod
    def handle_commit_errors(func: F) -> F:
        @wraps(func)
        async def exception_wrapper(
            self: "SQLAlchemyRepository[T]", *args: Any, **kwargs: Any
        ) -> Any:
            try:
                return await func(self, *args, **kwargs)
            except Exception as e:
                parsed_error = self._parse_integrity_error(e)
                if parsed_error is not e:
                    raise parsed_error from e
                raise

        return exception_wrapper  # type: ignore[return-value]

    @handle_commit_errors
    async def get(
        self,
        entity_id: uuid.UUID,
        raise_error: bool = True,
        response_model: type[BaseModel] | None = None,
    ) -> T | None:
        return await self._get_by_field_value("id", entity_id, raise_error, response_model)

    @handle_commit_errors
    async def get_by_field(
        self,
        field: str,
        value: Any,
        raise_error: bool = True,
        response_model: type[BaseModel] | None = None,
    ) -> T | None:
        return await self._get_by_field_value(field, value, raise_error, response_model)

    async def _get_by_field_value(
        self,
        field: str,
        value: Any,
        raise_error: bool,
        response_model: type[BaseModel] | None,
    ) -> T | None:
        if not (filter_model_field := getattr(self.model, field, None)):
            raise AttributeError(
                f"Field '{field}' not found in {self.model._display_name()}"
            )
        query: Select[Any] = select(self.model)
        if response_model:
            query = self._generate_select_from_pydantic(response_model)

        result = await self._session.execute(
            query.where(filter_model_field == value)
        )
        item = result.scalar()

        if item is None and raise_error:
            raise NotFoundError(
                detail=f"{self.model._display_name()} {value} not found"
            )
        return item

    async def get_all(
        self,
        entity_filter: BaseFilterModel | None = None,
        pagination_params: Params | None = None,
        options: "QueryOptions | None" = None,
    ) -> list[T] | Page[T]:
        from app.repositories.base_repository import QueryOptions as _QueryOptions

        opts = options or _QueryOptions()
        query = opts.base_query if opts.base_query is not None else self._base_query()
        if opts.response_model:
            query = self._generate_select_from_pydantic(opts.response_model, query)
        if entity_filter:
            query = entity_filter.filter(query)
            if hasattr(entity_filter, "sort"):
                query = entity_filter.sort(query)

        if pagination_params:
            # paginate returns Any due to dynamic params typing - explicit cast needed
            return await paginate(  # type: ignore[no-any-return, call-overload]
                self._session,
                query,
                params=pagination_params,
                **opts.pagination_kwargs,
            )

        if opts.return_scalars:
            result = await self._session.execute(query)  # type: ignore[call-overload]
            return list(result.scalars().all())

        result = await self._session.execute(query)  # type: ignore[call-overload]
        return list(result.all())

    @handle_commit_errors
    async def create(self, entity: BaseModel, **extra_fields: Any) -> T:
        """Create a single entity using INSERT ... RETURNING."""
        insert_dialect = self._get_insert_dialect()
        values = self._normalize_values(entity, **extra_fields)

        stmt = insert_dialect(self.model).values(values).returning(self.model)
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.scalar_one()

    @handle_commit_errors
    async def upsert(self, entity: BaseModel, **extra_fields: Any) -> T:
        """Insert or update based on primary key using INSERT ... ON CONFLICT DO UPDATE."""
        insert_dialect = self._get_insert_dialect()
        values = self._normalize_values(entity, **extra_fields)

        stmt = (
            insert_dialect(self.model)
            .values(values)
            .on_conflict_do_update(index_elements=["id"], set_=values)
            .returning(self.model)
        )
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.scalar_one()

    @handle_commit_errors
    async def update(
        self, entity_id: uuid.UUID, updated_entity: BaseModel | dict[str, Any]
    ) -> T:
        """Update an entity using UPDATE ... RETURNING."""
        updated_values = self._normalize_values(updated_entity, exclude_unset=True)

        stmt = (
            sql_update(self.model)
            .where(self.model.id == entity_id)  # type: ignore[attr-defined]
            .values(**updated_values)
            .returning(self.model)
        )

        result = await self._session.execute(stmt)
        await self._session.commit()

        updated = result.scalar_one_or_none()
        if updated is None:
            raise NotFoundError(
                detail=f"{self.model._display_name()} {entity_id} not found"
            )
        return updated

    @handle_commit_errors
    async def delete(self, entity_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(self.model).where(self.model.id == entity_id)  # type: ignore[attr-defined]
        )
        await self._session.commit()

    @handle_commit_errors
    async def create_many(
        self,
        entities: Sequence[BaseModel],
        on_conflict: OnConflictClause = do_default_on_conflict,
    ) -> list[T]:
        """Create multiple entities using bulk INSERT ... RETURNING."""
        if not entities:
            logger.warning("No entities to create")
            return []

        insert_dialect = self._get_insert_dialect()
        values = [entity.model_dump() for entity in entities]

        stmt = insert_dialect(self.model).values(values)
        stmt = on_conflict(stmt)

        result = await self._session.execute(stmt.returning(self.model))
        await self._session.commit()
        return list(result.scalars().all())

    @handle_commit_errors
    async def delete_many(self, delete_filter_query: Selectable) -> None:
        await self._session.execute(delete_filter_query)  # type: ignore[call-overload]
        await self._session.commit()
