"""Tests for QueryBuilder."""

import uuid
from unittest.mock import MagicMock, patch

from pydantic import BaseModel

from app.repositories.query_builder import QueryBuilder


class MockModel:
    """Mock SQLAlchemy model for testing."""

    __tablename__ = "mock_table"


class MockSchema(BaseModel):
    """Mock Pydantic schema for testing."""

    id: uuid.UUID
    name: str


class TestQueryBuilderInit:
    """Tests for QueryBuilder initialization."""

    def test_init_sets_model(self):
        """Test that model is set on initialization."""
        builder = QueryBuilder(MockModel)

        assert builder.model == MockModel


class TestQueryBuilderBuildSelectFromPydantic:
    """Tests for build_select_from_pydantic method."""

    @patch("app.repositories.query_builder.select_from_pydantic")
    @patch("app.repositories.query_builder.select")
    def test_creates_select_with_options(self, mock_select, mock_select_from_pydantic):
        """Test that select statement is created with options."""
        mock_options = [MagicMock()]
        mock_select_from_pydantic.return_value = mock_options
        mock_select_stmt = MagicMock()
        mock_select_stmt.options.return_value = mock_select_stmt
        mock_select.return_value = mock_select_stmt

        builder = QueryBuilder(MockModel)
        result = builder.build_select_from_pydantic(MockSchema)

        mock_select_from_pydantic.assert_called_once_with(MockModel, MockSchema)
        mock_select.assert_called_once_with(MockModel)
        mock_select_stmt.options.assert_called_once()

    @patch("app.repositories.query_builder.select_from_pydantic")
    @patch("app.repositories.query_builder.select")
    def test_extends_existing_query(self, mock_select, mock_select_from_pydantic):
        """Test that existing query is extended when provided."""
        mock_options = [MagicMock()]
        mock_select_from_pydantic.return_value = mock_options
        existing_query = MagicMock()
        existing_query.options.return_value = existing_query

        builder = QueryBuilder(MockModel)
        result = builder.build_select_from_pydantic(MockSchema, query=existing_query)

        existing_query.options.assert_called_once()
        assert result == existing_query

    @patch("app.repositories.query_builder.select_from_pydantic")
    @patch("app.repositories.query_builder.select")
    def test_returns_base_select_when_no_query(self, mock_select, mock_select_from_pydantic):
        """Test that base select is returned when no query provided."""
        mock_options = []
        mock_select_from_pydantic.return_value = mock_options
        mock_select_stmt = MagicMock()
        mock_select_stmt.options.return_value = mock_select_stmt
        mock_select.return_value = mock_select_stmt

        builder = QueryBuilder(MockModel)
        result = builder.build_select_from_pydantic(MockSchema, query=None)

        assert result == mock_select_stmt


class TestQueryBuilderModelAttribute:
    """Tests for QueryBuilder model attribute."""

    def test_model_is_stored(self):
        """Test that model is stored correctly."""
        builder = QueryBuilder(MockModel)
        assert builder.model is MockModel

    def test_different_models(self):
        """Test with different models."""

        class AnotherModel:
            __tablename__ = "another"

        builder1 = QueryBuilder(MockModel)
        builder2 = QueryBuilder(AnotherModel)

        assert builder1.model is MockModel
        assert builder2.model is AnotherModel
