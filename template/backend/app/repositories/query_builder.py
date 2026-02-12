"""Query builder for SQLAlchemy repositories."""

from typing import Any

from pydantic import BaseModel
from sqlalchemy import Selectable, select
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import Select

from app.database.db.statement_generator import select_from_pydantic


class QueryBuilder:
    """Handles SQLAlchemy query construction with Pydantic models."""

    def __init__(self, model: type[DeclarativeBase]) -> None:
        self.model = model

    def build_select_from_pydantic(
        self,
        pydantic_model: type[BaseModel],
        query: Selectable | None = None,
    ) -> Select[Any]:
        """Build a select statement with optimized eager loading.

        Args:
            pydantic_model: The Pydantic schema to base loading on
            query: Existing query to extend, or None to create new

        Returns:
            A select statement with appropriate eager loading options
        """
        options = select_from_pydantic(self.model, pydantic_model)
        # select_from_pydantic returns Sequence[Load | None] which mypy doesn't recognize
        # as compatible with ExecutableOption. This is a known limitation of the Load types.
        base_select: Select[Any] = select(self.model).options(*options)
        if query is not None:
            return query.options(*options)  # type: ignore[attr-defined, no-any-return]
        return base_select
