"""Tests for BaseService CRUD operations."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel

from app.services.base_crud_service import BaseService


@pytest.fixture
def sample_entity_id():
    """Generate a sample entity UUID for CRUD tests."""
    return uuid.UUID("87654321-4321-8765-4321-876543218765")


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
    def service(self, mock_team_repository):
        """Create a BaseService instance with mocked repository."""
        return BaseService(repo=mock_team_repository)

    async def test_get_by_id_success(
        self, service, mock_team_repository, sample_entity_id
    ):
        """Test successful get_by_id."""
        expected = MockModel(id=sample_entity_id, name="Test")
        mock_team_repository.get.return_value = expected

        result = await service.get_by_id(sample_entity_id)

        mock_team_repository.get.assert_called_once_with(
            sample_entity_id, raise_error=True
        )
        assert result == expected

    async def test_get_by_id_with_raise_error_false(
        self, service, mock_team_repository, sample_entity_id
    ):
        """Test get_by_id with raise_error=False."""
        mock_team_repository.get.return_value = None

        result = await service.get_by_id(sample_entity_id, raise_error=False)

        mock_team_repository.get.assert_called_once_with(
            sample_entity_id, raise_error=False
        )
        assert result is None


class TestBaseServiceGetAll:
    """Tests for BaseService.get_all method."""

    @pytest.fixture
    def service(self, mock_team_repository):
        return BaseService(repo=mock_team_repository)

    async def test_get_all_no_filter(self, service, mock_team_repository):
        """Test get_all without filter."""
        expected = [MockModel(id=uuid.uuid4(), name="Item 1")]
        mock_team_repository.get_all.return_value = expected

        result = await service.get_all()

        mock_team_repository.get_all.assert_called_once_with(None, None)
        assert result == expected

    async def test_get_all_with_filter(self, service, mock_team_repository):
        """Test get_all with filter."""
        mock_filter = MagicMock()
        expected = [MockModel(id=uuid.uuid4(), name="Filtered")]
        mock_team_repository.get_all.return_value = expected

        result = await service.get_all(entity_filter=mock_filter)

        mock_team_repository.get_all.assert_called_once_with(mock_filter, None)
        assert result == expected

    async def test_get_all_paginated(self, service, mock_team_repository):
        """Test get_all_paginated delegates to repo with correct args."""
        from fastapi_pagination import Params

        params = Params(page=1, size=10)
        mock_page = MagicMock()
        mock_team_repository.get_all_paginated = AsyncMock(return_value=mock_page)

        result = await service.get_all_paginated(pagination_params=params)

        mock_team_repository.get_all_paginated.assert_called_once_with(
            params, None, None
        )
        assert result == mock_page


class TestBaseServiceCreate:
    """Tests for BaseService.create method."""

    @pytest.fixture
    def service(self, mock_team_repository):
        return BaseService(repo=mock_team_repository)

    async def test_create_success(self, service, mock_team_repository):
        """Test successful create."""
        entity = MockEntity(id=uuid.uuid4(), name="New Item")
        expected = MockModel(id=entity.id, name=entity.name)
        mock_team_repository.create.return_value = expected

        result = await service.create(entity)

        mock_team_repository.create.assert_called_once_with(entity)
        assert result == expected

    async def test_create_with_extra_fields(self, service, mock_team_repository):
        """Test create with extra fields."""
        entity = MockEntity(id=uuid.uuid4(), name="New Item")
        expected = MockModel(id=entity.id, name=entity.name)
        mock_team_repository.create.return_value = expected

        result = await service.create(entity, extra_field="value")

        mock_team_repository.create.assert_called_once_with(entity, extra_field="value")
        assert result == expected


class TestBaseServiceCreateMany:
    """Tests for BaseService.create_many method."""

    @pytest.fixture
    def service(self, mock_team_repository):
        return BaseService(repo=mock_team_repository)

    async def test_create_many_success(self, service, mock_team_repository):
        """Test successful create_many."""
        entities = [
            MockEntity(id=uuid.uuid4(), name="Item 1"),
            MockEntity(id=uuid.uuid4(), name="Item 2"),
        ]
        expected = [MockModel(id=e.id, name=e.name) for e in entities]
        mock_team_repository.create_many.return_value = expected

        result = await service.create_many(entities)

        mock_team_repository.create_many.assert_called_once()
        assert result == expected


class TestBaseServiceUpsert:
    """Tests for BaseService.upsert method."""

    @pytest.fixture
    def service(self, mock_team_repository):
        return BaseService(repo=mock_team_repository)

    async def test_upsert_success(self, service, mock_team_repository):
        """Test successful upsert."""
        entity = MockEntity(id=uuid.uuid4(), name="Upserted")
        expected = MockModel(id=entity.id, name=entity.name)
        mock_team_repository.upsert.return_value = expected

        result = await service.upsert(entity)

        mock_team_repository.upsert.assert_called_once_with(entity)
        assert result == expected


class TestBaseServiceUpdate:
    """Tests for BaseService.update method."""

    @pytest.fixture
    def service(self, mock_team_repository):
        return BaseService(repo=mock_team_repository)

    async def test_update_success(
        self, service, mock_team_repository, sample_entity_id
    ):
        """Test successful update."""
        entity = MockEntity(id=sample_entity_id, name="Updated")
        expected = MockModel(id=sample_entity_id, name="Updated")
        mock_team_repository.update.return_value = expected

        result = await service.update(sample_entity_id, entity)

        mock_team_repository.update.assert_called_once_with(sample_entity_id, entity)
        assert result == expected


class TestBaseServiceDelete:
    """Tests for BaseService.delete method."""

    @pytest.fixture
    def service(self, mock_team_repository):
        return BaseService(repo=mock_team_repository)

    async def test_delete_success(
        self, service, mock_team_repository, sample_entity_id
    ):
        """Test successful delete."""
        mock_team_repository.delete.return_value = None

        result = await service.delete(sample_entity_id)

        mock_team_repository.delete.assert_called_once_with(sample_entity_id)
        assert result is None
