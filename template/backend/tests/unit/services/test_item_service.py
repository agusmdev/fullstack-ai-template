"""Tests for ItemService."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.items.schemas import ItemCreate, ItemUpdate
from app.modules.items.service import ItemService
from app.repositories.exceptions import NotFoundError


class TestItemServiceGetBySku:
    """Tests for ItemService.get_by_sku method."""

    @pytest.fixture
    def service(self, mock_item_repository):
        return ItemService(repo=mock_item_repository)

    async def test_get_by_sku_success(
        self, service, mock_item_repository, sample_item_model
    ):
        """Test successful get_by_sku."""
        mock_item_repository.get.return_value = sample_item_model

        result = await service.get_by_sku("TEST-SKU-001")

        mock_item_repository.get.assert_called_once_with(
            "TEST-SKU-001", filter_field="sku", raise_error=False
        )
        assert result == sample_item_model

    async def test_get_by_sku_not_found(self, service, mock_item_repository):
        """Test get_by_sku when SKU doesn't exist."""
        mock_item_repository.get.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            await service.get_by_sku("NONEXISTENT-SKU")

        assert "NONEXISTENT-SKU" in exc_info.value.detail


class TestItemServiceCreate:
    """Tests for ItemService.create method."""

    @pytest.fixture
    def service(self, mock_item_repository):
        return ItemService(repo=mock_item_repository)

    async def test_create_success(self, service, mock_item_repository, sample_item_model):
        """Test successful item creation."""
        mock_item_repository.create.return_value = sample_item_model
        create_data = ItemCreate(
            name="New Item",
            description="A new item",
            quantity=5,
            sku="NEW-SKU-001",
        )

        result = await service.create(create_data)

        mock_item_repository.create.assert_called_once_with(create_data)
        assert result == sample_item_model

    async def test_create_with_extra_fields(
        self, service, mock_item_repository, sample_item_model
    ):
        """Test create with extra fields."""
        mock_item_repository.create.return_value = sample_item_model
        create_data = ItemCreate(name="Test", quantity=1)

        result = await service.create(create_data, extra_field="value")

        mock_item_repository.create.assert_called_once_with(
            create_data, extra_field="value"
        )


class TestItemServiceUpdate:
    """Tests for ItemService.update method."""

    @pytest.fixture
    def service(self, mock_item_repository):
        return ItemService(repo=mock_item_repository)

    async def test_update_success(
        self, service, mock_item_repository, sample_item_model, sample_item_id
    ):
        """Test successful item update."""
        updated_item = MagicMock()
        updated_item.id = sample_item_id
        updated_item.name = "Updated Name"
        mock_item_repository.update.return_value = updated_item
        update_data = ItemUpdate(name="Updated Name")

        result = await service.update(sample_item_id, update_data)

        mock_item_repository.update.assert_called_once_with(sample_item_id, update_data)
        assert result == updated_item

    async def test_update_partial(
        self, service, mock_item_repository, sample_item_model, sample_item_id
    ):
        """Test partial item update."""
        mock_item_repository.update.return_value = sample_item_model
        update_data = ItemUpdate(quantity=99)

        result = await service.update(sample_item_id, update_data)

        mock_item_repository.update.assert_called_once()
        assert result == sample_item_model


class TestItemServiceInheritedMethods:
    """Tests for inherited BaseService methods in ItemService."""

    @pytest.fixture
    def service(self, mock_item_repository):
        return ItemService(repo=mock_item_repository)

    async def test_get_by_id(self, service, mock_item_repository, sample_item_model):
        """Test inherited get_by_id method."""
        mock_item_repository.get.return_value = sample_item_model

        result = await service.get_by_id(sample_item_model.id)

        mock_item_repository.get.assert_called_once_with(
            sample_item_model.id, raise_error=True
        )
        assert result == sample_item_model

    async def test_get_all(self, service, mock_item_repository):
        """Test inherited get_all method."""
        mock_items = [MagicMock(), MagicMock()]
        mock_item_repository.get_all.return_value = mock_items

        result = await service.get_all()

        mock_item_repository.get_all.assert_called_once()
        assert result == mock_items

    async def test_delete(self, service, mock_item_repository, sample_item_id):
        """Test inherited delete method."""
        mock_item_repository.delete.return_value = None

        await service.delete(sample_item_id)

        mock_item_repository.delete.assert_called_once_with(sample_item_id)

    async def test_upsert(self, service, mock_item_repository, sample_item_model):
        """Test inherited upsert method."""
        mock_item_repository.upsert.return_value = sample_item_model
        entity = ItemCreate(name="Upsert Item", quantity=1)

        result = await service.upsert(entity)

        mock_item_repository.upsert.assert_called_once_with(entity)
        assert result == sample_item_model

    async def test_create_many(self, service, mock_item_repository):
        """Test inherited create_many method."""
        items_to_create = [
            ItemCreate(name="Item 1", quantity=1),
            ItemCreate(name="Item 2", quantity=2),
        ]
        created_items = [MagicMock(), MagicMock()]
        mock_item_repository.create_many.return_value = created_items

        result = await service.create_many(items_to_create)

        mock_item_repository.create_many.assert_called_once()
        assert result == created_items
