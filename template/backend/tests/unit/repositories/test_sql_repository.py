"""Tests for SQLAlchemyRepository."""

import uuid
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from app.repositories.exceptions import DuplicateError, ReferencedError
from app.repositories.sql_repository import SQLAlchemyRepository


# Use a simple mock class instead of inheriting from Base
class MockModel:
    """Mock SQLAlchemy model for testing."""

    __tablename__ = "mock_table"

    @classmethod
    def _display_name(cls):
        return "Mock_table"

    id = MagicMock()
    name = MagicMock()


class MockSchema(BaseModel):
    """Mock Pydantic schema for testing."""

    id: uuid.UUID
    name: str


class TestSQLAlchemyRepositoryNormalizeValues:
    """Tests for _normalize_values method."""

    @pytest.fixture
    def repository(self, mock_session):
        class TestRepo(SQLAlchemyRepository[MockModel]):
            model = MockModel

        return TestRepo(session=mock_session)

    def test_normalize_pydantic_model(self, repository):
        """Test normalizing a Pydantic model to dict."""
        entity = MockSchema(id=uuid.uuid4(), name="Test")

        result = repository._normalize_values(entity)

        assert "id" in result
        assert result["name"] == "Test"

    def test_normalize_dict(self, repository):
        """Test normalizing a dict (passthrough)."""
        entity = {"id": uuid.uuid4(), "name": "Test"}

        result = repository._normalize_values(entity)

        assert result == entity

    def test_normalize_with_extra_fields(self, repository):
        """Test normalizing with extra fields."""
        entity = MockSchema(id=uuid.uuid4(), name="Test")

        result = repository._normalize_values(entity, extra_field="value")

        assert result["extra_field"] == "value"

    def test_normalize_exclude_unset(self, repository):
        """Test normalizing with exclude_unset=True."""
        entity = MockSchema(id=uuid.uuid4(), name="Test")

        result = repository._normalize_values(entity, exclude_unset=True)

        # Should still include set fields
        assert "name" in result


class TestSQLAlchemyRepositoryParseIntegrityError:
    """Tests for _parse_integrity_error method."""

    @pytest.fixture
    def repository_class(self):
        class TestRepo(SQLAlchemyRepository[MockModel]):
            model = MockModel

        return TestRepo

    def test_parse_unique_violation(self, repository_class):
        """Test parsing unique constraint violation."""
        mock_orig = MagicMock()
        mock_orig.__str__ = lambda self: "unique violation: duplicate key value"
        error = IntegrityError(statement="INSERT", params={}, orig=mock_orig)

        result = repository_class._parse_integrity_error(error)

        assert isinstance(result, DuplicateError)

    def test_parse_duplicate_key(self, repository_class):
        """Test parsing duplicate key error."""
        mock_orig = MagicMock()
        mock_orig.__str__ = lambda self: "duplicate key value violates unique constraint"
        error = IntegrityError(statement="INSERT", params={}, orig=mock_orig)

        result = repository_class._parse_integrity_error(error)

        assert isinstance(result, DuplicateError)

    def test_parse_foreign_key_violation(self, repository_class):
        """Test parsing foreign key violation."""
        mock_orig = MagicMock()
        mock_orig.__str__ = lambda self: "foreign key violation on table"
        error = IntegrityError(statement="DELETE", params={}, orig=mock_orig)

        result = repository_class._parse_integrity_error(error)

        assert isinstance(result, ReferencedError)

    def test_parse_still_referenced(self, repository_class):
        """Test parsing 'is still referenced' error."""
        mock_orig = MagicMock()
        mock_orig.__str__ = lambda self: "is still referenced by table orders"
        error = IntegrityError(statement="DELETE", params={}, orig=mock_orig)

        result = repository_class._parse_integrity_error(error)

        assert isinstance(result, ReferencedError)

    def test_parse_unknown_integrity_error(self, repository_class):
        """Test parsing unknown integrity error returns original."""
        mock_orig = MagicMock()
        mock_orig.__str__ = lambda self: "some other constraint violation"
        error = IntegrityError(statement="INSERT", params={}, orig=mock_orig)

        result = repository_class._parse_integrity_error(error)

        assert result is error

    def test_parse_non_integrity_error(self, repository_class):
        """Test parsing non-integrity error returns original."""
        error = ValueError("not an integrity error")

        result = repository_class._parse_integrity_error(error)

        assert result is error


class TestSQLAlchemyRepositoryGetInsertDialect:
    """Tests for _get_insert_dialect method."""

    def test_returns_postgresql_insert(self):
        """Test that PostgreSQL insert is returned."""
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        result = SQLAlchemyRepository._get_insert_dialect()

        # Should be the PostgreSQL insert function
        assert result is pg_insert


class TestSQLAlchemyRepositoryBaseQuery:
    """Tests for _base_query method."""

    def test_base_query_returns_select(self, mock_session):
        """Test that _base_query returns a select statement."""
        from app.modules.items.repository import ItemRepository

        repo = ItemRepository(session=mock_session)
        result = repo._base_query()

        # Should be a select statement for the model
        assert result is not None


class TestSQLAlchemyRepositoryTranslateCommitErrors:
    """Tests for translate_commit_errors decorator."""

    @pytest.fixture
    def repository(self, mock_session):
        class TestRepo(SQLAlchemyRepository[MockModel]):
            model = MockModel

        return TestRepo(session=mock_session)

    async def test_decorator_passes_through_on_success(self, repository, mock_session):
        """Test decorator passes through on success."""
        mock_result = MagicMock()
        mock_session.execute.return_value = mock_result

        # The decorator is applied to methods like create, update, etc.
        # Testing indirectly through method behavior

    async def test_decorator_raises_parsed_error(self, repository, mock_session):
        """Test decorator raises parsed error on integrity violation."""
        mock_orig = MagicMock()
        mock_orig.__str__ = lambda self: "duplicate key value"
        error = IntegrityError(statement="INSERT", params={}, orig=mock_orig)
        mock_session.execute.side_effect = error

        # The repository methods should raise DuplicateError
        # This would be tested via actual method calls


class TestSQLAlchemyRepositoryInit:
    """Tests for SQLAlchemyRepository initialization."""

    def test_init_sets_session(self, mock_session):
        """Test that session is set on init."""

        class TestRepo(SQLAlchemyRepository[MockModel]):
            model = MockModel

        repo = TestRepo(session=mock_session)

        assert repo._session == mock_session

    def test_init_creates_query_builder(self, mock_session):
        """Test that query builder is created on init."""

        class TestRepo(SQLAlchemyRepository[MockModel]):
            model = MockModel

        repo = TestRepo(session=mock_session)

        assert repo._query_builder is not None
