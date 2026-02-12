"""Tests for BaseService CRUD operations."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel

from app.services.base_crud_service import BaseService


class MockEntity(BaseModel):
    """Mock entity for testing."""

    id: uuid.UUID
    name: str


class MockModel:
    """Mock SQLAlchemy model."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestBaseServiceGetById:
    """Tests for BaseService.get_by_id method."""

    @pytest.fixture
    def service(self, mock_item_repository):
        """Create a BaseService instance with mocked repository."""
        return BaseService(repo=mock_item_repository)

    async def test_get_by_id_success(self, service, mock_item_repository, sample_item_id):
        """Test successful get_by_id."""
        expected = MockModel(id=sample_item_id, name="Test")
        mock_item_repository.get.return_value = expected

        result = await service.get_by_id(sample_item_id)

        mock_item_repository.get.assert_called_once_with(sample_item_id, raise_error=True)
        assert result == expected

    async def test_get_by_id_with_raise_error_false(
        self, service, mock_item_repository, sample_item_id
    ):
        """Test get_by_id with raise_error=False."""
        mock_item_repository.get.return_value = None

        result = await service.get_by_id(sample_item_id, raise_error=False)

        mock_item_repository.get.assert_called_once_with(sample_item_id, raise_error=False)
        assert result is None


class TestBaseServiceGetAll:
    """Tests for BaseService.get_all method."""

    @pytest.fixture
    def service(self, mock_item_repository):
        return BaseService(repo=mock_item_repository)

    async def test_get_all_no_filter(self, service, mock_item_repository):
        """Test get_all without filter."""
        expected = [MockModel(id=uuid.uuid4(), name="Item 1")]
        mock_item_repository.get_all.return_value = expected

        result = await service.get_all()

        mock_item_repository.get_all.assert_called_once_with(None, None)
        assert result == expected

    async def test_get_all_with_filter(self, service, mock_item_repository):
        """Test get_all with filter."""
        mock_filter = MagicMock()
        expected = [MockModel(id=uuid.uuid4(), name="Filtered")]
        mock_item_repository.get_all.return_value = expected

        result = await service.get_all(entity_filter=mock_filter)

        mock_item_repository.get_all.assert_called_once_with(mock_filter, None)
        assert result == expected

    async def test_get_all_with_pagination(self, service, mock_item_repository):
        """Test get_all with pagination params."""
        from fastapi_pagination import Params

        params = Params(page=1, size=10)
        mock_page = MagicMock()
        mock_item_repository.get_all.return_value = mock_page

        result = await service.get_all(pagination_params=params)

        mock_item_repository.get_all.assert_called_once_with(None, params)
        assert result == mock_page


class TestBaseServiceCreate:
    """Tests for BaseService.create method."""

    @pytest.fixture
    def service(self, mock_item_repository):
        return BaseService(repo=mock_item_repository)

    async def test_create_success(self, service, mock_item_repository):
        """Test successful create."""
        entity = MockEntity(id=uuid.uuid4(), name="New Item")
        expected = MockModel(id=entity.id, name=entity.name)
        mock_item_repository.create.return_value = expected

        result = await service.create(entity)

        mock_item_repository.create.assert_called_once_with(entity)
        assert result == expected

    async def test_create_with_extra_fields(self, service, mock_item_repository):
        """Test create with extra fields."""
        entity = MockEntity(id=uuid.uuid4(), name="New Item")
        expected = MockModel(id=entity.id, name=entity.name)
        mock_item_repository.create.return_value = expected

        result = await service.create(entity, extra_field="value")

        mock_item_repository.create.assert_called_once_with(entity, extra_field="value")
        assert result == expected


class TestBaseServiceCreateMany:
    """Tests for BaseService.create_many method."""

    @pytest.fixture
    def service(self, mock_item_repository):
        return BaseService(repo=mock_item_repository)

    async def test_create_many_success(self, service, mock_item_repository):
        """Test successful create_many."""
        entities = [
            MockEntity(id=uuid.uuid4(), name="Item 1"),
            MockEntity(id=uuid.uuid4(), name="Item 2"),
        ]
        expected = [MockModel(id=e.id, name=e.name) for e in entities]
        mock_item_repository.create_many.return_value = expected

        result = await service.create_many(entities)

        mock_item_repository.create_many.assert_called_once()
        assert result == expected


class TestBaseServiceUpsert:
    """Tests for BaseService.upsert method."""

    @pytest.fixture
    def service(self, mock_item_repository):
        return BaseService(repo=mock_item_repository)

    async def test_upsert_success(self, service, mock_item_repository):
        """Test successful upsert."""
        entity = MockEntity(id=uuid.uuid4(), name="Upserted")
        expected = MockModel(id=entity.id, name=entity.name)
        mock_item_repository.upsert.return_value = expected

        result = await service.upsert(entity)

        mock_item_repository.upsert.assert_called_once_with(entity)
        assert result == expected


class TestBaseServiceUpdate:
    """Tests for BaseService.update method."""

    @pytest.fixture
    def service(self, mock_item_repository):
        return BaseService(repo=mock_item_repository)

    async def test_update_success(self, service, mock_item_repository, sample_item_id):
        """Test successful update."""
        entity = MockEntity(id=sample_item_id, name="Updated")
        expected = MockModel(id=sample_item_id, name="Updated")
        mock_item_repository.update.return_value = expected

        result = await service.update(sample_item_id, entity)

        mock_item_repository.update.assert_called_once_with(sample_item_id, entity)
        assert result == expected


class TestBaseServiceDelete:
    """Tests for BaseService.delete method."""

    @pytest.fixture
    def service(self, mock_item_repository):
        return BaseService(repo=mock_item_repository)

    async def test_delete_success(self, service, mock_item_repository, sample_item_id):
        """Test successful delete."""
        mock_item_repository.delete.return_value = None

        result = await service.delete(sample_item_id)

        mock_item_repository.delete.assert_called_once_with(sample_item_id)
        assert result is None
