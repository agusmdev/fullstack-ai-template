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
        self, service, mock_item_repository, sample_item_model, sample_item_owner_id
    ):
        """Test successful get_by_sku."""
        mock_item_repository.get_by_field.return_value = sample_item_model

        result = await service.get_by_sku("TEST-SKU-001", user_id=sample_item_owner_id)

        mock_item_repository.get_by_field.assert_called_once_with(
            "sku", "TEST-SKU-001", raise_error=False
        )
        assert result == sample_item_model

    async def test_get_by_sku_not_found(self, service, mock_item_repository, sample_item_owner_id):
        """Test get_by_sku when SKU doesn't exist."""
        mock_item_repository.get_by_field.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            await service.get_by_sku("NONEXISTENT-SKU", user_id=sample_item_owner_id)

        assert "NONEXISTENT-SKU" in exc_info.value.detail

    async def test_get_by_sku_wrong_owner(
        self, service, mock_item_repository, sample_item_model
    ):
        """Test get_by_sku raises NotFoundError when caller is not the owner."""
        mock_item_repository.get_by_field.return_value = sample_item_model
        other_user_id = uuid.uuid4()

        with pytest.raises(NotFoundError):
            await service.get_by_sku("TEST-SKU-001", user_id=other_user_id)


class TestItemServiceCreate:
    """Tests for ItemService.create method."""

    @pytest.fixture
    def service(self, mock_item_repository):
        return ItemService(repo=mock_item_repository)

    async def test_create_success(
        self, service, mock_item_repository, sample_item_model, sample_item_owner_id
    ):
        """Test successful item creation with user_id."""
        mock_item_repository.create.return_value = sample_item_model
        create_data = ItemCreate(name="New Item", description="A new item")

        result = await service.create(create_data, user_id=sample_item_owner_id)

        mock_item_repository.create.assert_called_once_with(
            create_data, user_id=sample_item_owner_id
        )
        assert result == sample_item_model

    async def test_create_requires_user_id(self, service):
        """Test that create requires user_id."""
        create_data = ItemCreate(name="Test")

        with pytest.raises(TypeError):
            await service.create(create_data)  # type: ignore[call-arg]


class TestItemServiceUpdate:
    """Tests for ItemService.update method (with ownership check)."""

    @pytest.fixture
    def service(self, mock_item_repository):
        return ItemService(repo=mock_item_repository)

    async def test_update_success(
        self, service, mock_item_repository, sample_item_model, sample_item_id, sample_item_owner_id
    ):
        """Test successful item update by owner."""
        mock_item_repository.get.return_value = sample_item_model
        updated_item = MagicMock()
        updated_item.id = sample_item_id
        updated_item.name = "Updated Name"
        mock_item_repository.update.return_value = updated_item
        update_data = ItemUpdate(name="Updated Name")

        result = await service.update(sample_item_id, update_data, user_id=sample_item_owner_id)

        mock_item_repository.update.assert_called_once_with(sample_item_id, update_data)
        assert result == updated_item

    async def test_update_rejected_for_non_owner(
        self, service, mock_item_repository, sample_item_model, sample_item_id
    ):
        """Test that update raises NotFoundError when caller does not own the item."""
        mock_item_repository.get.return_value = sample_item_model
        other_user_id = uuid.uuid4()

        with pytest.raises(NotFoundError):
            await service.update(sample_item_id, ItemUpdate(name="x"), user_id=other_user_id)

        mock_item_repository.update.assert_not_called()

    async def test_update_partial(
        self, service, mock_item_repository, sample_item_model, sample_item_id, sample_item_owner_id
    ):
        """Test partial item update."""
        mock_item_repository.get.return_value = sample_item_model
        mock_item_repository.update.return_value = sample_item_model

        result = await service.update(sample_item_id, ItemUpdate(name="x"), user_id=sample_item_owner_id)

        mock_item_repository.update.assert_called_once()
        assert result == sample_item_model


class TestItemServiceDelete:
    """Tests for ItemService.delete method (with ownership check)."""

    @pytest.fixture
    def service(self, mock_item_repository):
        return ItemService(repo=mock_item_repository)

    async def test_delete_success(
        self, service, mock_item_repository, sample_item_model, sample_item_id, sample_item_owner_id
    ):
        """Test successful item deletion by owner."""
        mock_item_repository.get.return_value = sample_item_model
        mock_item_repository.delete.return_value = None

        await service.delete(sample_item_id, user_id=sample_item_owner_id)

        mock_item_repository.delete.assert_called_once_with(sample_item_id)

    async def test_delete_rejected_for_non_owner(
        self, service, mock_item_repository, sample_item_model, sample_item_id
    ):
        """Test that delete raises NotFoundError when caller does not own the item."""
        mock_item_repository.get.return_value = sample_item_model
        other_user_id = uuid.uuid4()

        with pytest.raises(NotFoundError):
            await service.delete(sample_item_id, user_id=other_user_id)

        mock_item_repository.delete.assert_not_called()


class TestItemServiceInheritedMethods:
    """Tests for inherited BaseService methods in ItemService."""

    @pytest.fixture
    def service(self, mock_item_repository):
        return ItemService(repo=mock_item_repository)

    async def test_get_by_id(
        self, service, mock_item_repository, sample_item_model, sample_item_owner_id
    ):
        """Test overridden get_by_id method (enforces ownership)."""
        mock_item_repository.get.return_value = sample_item_model

        result = await service.get_by_id(sample_item_model.id, user_id=sample_item_owner_id)

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

    async def test_upsert(self, service, mock_item_repository, sample_item_model):
        """Test inherited upsert method."""
        mock_item_repository.upsert.return_value = sample_item_model
        entity = ItemCreate(name="Upsert Item")

        result = await service.upsert(entity)

        mock_item_repository.upsert.assert_called_once_with(entity)
        assert result == sample_item_model

    async def test_create_many(self, service, mock_item_repository):
        """Test inherited create_many method."""
        items_to_create = [
            ItemCreate(name="Item 1"),
            ItemCreate(name="Item 2"),
        ]
        created_items = [MagicMock(), MagicMock()]
        mock_item_repository.create_many.return_value = created_items

        result = await service.create_many(items_to_create)

        mock_item_repository.create_many.assert_called_once()
        assert result == created_items
