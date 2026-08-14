"""Tests for QueryBuilder.

These tests exercise QueryBuilder against real SQLAlchemy models and assert on the
*behavior* of the produced Select statements (FROM target, load_only column set,
option attachment) rather than mocking the underlying helpers and only checking
that they were called.
"""

import uuid

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase

from app.database.base import Base
from app.modules.items.models import Item
from app.modules.items.schemas import ItemResponse
from app.repositories.query_builder import QueryBuilder


def _compiled(stmt) -> str:
    """Compile a Select to SQL with literal binds for behavioral assertions."""
    return str(stmt.compile(compile_kwargs={"literal_binds": True})).replace("\n", " ")


class TestQueryBuilderInit:
    """Tests for QueryBuilder initialization."""

    def test_init_sets_model(self):
        builder = QueryBuilder(Item)
        assert builder.model is Item

    def test_model_is_stored_for_any_declarative(self):
        class Other(DeclarativeBase):
            pass

        builder = QueryBuilder(Other)
        assert builder.model is Other


class TestBuildSelectFromPydantic:
    """Behavioral tests for build_select_from_pydantic."""

    def test_selects_only_schema_columns_via_load_only(self):
        """The statement should restrict to the Pydantic schema's columns."""
        builder = QueryBuilder(Item)

        stmt = builder.build_select_from_pydantic(ItemResponse)

        compiled = _compiled(stmt)
        # ItemResponse declares id, user_id, name, description — and only those
        # columns should appear in the emitted SELECT (load_only behavior).
        assert "item.id" in compiled
        assert "item.user_id" in compiled
        assert "item.name" in compiled
        assert "item.description" in compiled
        # Columns absent from the schema must not be eagerly loaded.
        assert "item.quantity" not in compiled
        assert "item.sku" not in compiled
        # The FROM target is the model's table.
        assert "FROM item" in compiled

    def test_options_list_matches_schema_fields(self):
        """The emitted SELECT lists exactly the schema's columns (load_only)."""
        builder = QueryBuilder(Item)

        stmt = builder.build_select_from_pydantic(ItemResponse)

        select_clause = _compiled(stmt).split(" FROM ")[0]
        loaded = {col.strip() for col in select_clause.replace("SELECT", "").split(",")}
        assert loaded == {"item.id", "item.user_id", "item.name", "item.description"}

    def test_extends_existing_query_with_load_only(self):
        """A provided query is returned with the schema's load options layered on."""
        builder = QueryBuilder(Item)
        existing = select(Item)

        stmt = builder.build_select_from_pydantic(ItemResponse, query=existing)

        # .options() returns a new statement, so identity is not preserved — but the
        # result must still target the model and carry the load_only restriction.
        compiled = _compiled(stmt)
        assert "FROM item" in compiled
        select_clause = compiled.split(" FROM ")[0]
        loaded = {col.strip() for col in select_clause.replace("SELECT", "").split(",")}
        assert loaded == {"item.id", "item.user_id", "item.name", "item.description"}

    def test_returns_new_select_when_no_query(self):
        """When query is None, a fresh Select targeting the model is built."""
        builder = QueryBuilder(Item)

        stmt = builder.build_select_from_pydantic(ItemResponse, query=None)

        assert stmt is not None
        assert "FROM item" in _compiled(stmt)

    def test_minimal_schema_loads_subset(self):
        """A schema with fewer fields produces a narrower column set."""

        class IdOnly(BaseModel):
            id: uuid.UUID

        builder = QueryBuilder(Item)

        stmt = builder.build_select_from_pydantic(IdOnly)

        compiled = _compiled(stmt)
        assert "item.id" in compiled
        assert "item.name" not in compiled
        assert "item.user_id" not in compiled


class TestQueryBuilderIntrospection:
    """Sanity checks on the builder's own state."""

    def test_model_attribute_exposed(self):
        builder = QueryBuilder(Item)
        assert hasattr(builder, "model")
        assert builder.model.__tablename__ == "item"

    def test_base_subclass_accepted(self):
        """QueryBuilder accepts any model that subclasses the declarative Base."""
        builder = QueryBuilder(Item)
        assert issubclass(builder.model, Base)
