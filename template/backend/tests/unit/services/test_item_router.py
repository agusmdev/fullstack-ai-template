"""Tests for Items router endpoint functions."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.items.routers import (
    create_item,
    delete_item,
    get_item,
    get_item_by_sku,
    list_items,
    update_item,
)
from app.modules.items.schemas import ItemCreate, ItemResponse, ItemUpdate


@pytest.fixture
def mock_item_service():
    svc = MagicMock()
    svc.get_by_id = AsyncMock()
    svc.get_all = AsyncMock()
    svc.create = AsyncMock()
    svc.update = AsyncMock()
    svc.delete = AsyncMock()
    svc.get_by_sku = AsyncMock()
    return svc


@pytest.fixture
def sample_item_id():
    return uuid.UUID("87654321-4321-8765-4321-876543218765")


@pytest.fixture
def sample_item_response(sample_item_id):
    item = MagicMock()
    item.id = sample_item_id
    item.name = "Test Item"
    item.description = "A test item"
    return item


class TestListItems:
    async def test_calls_service_get_all(self, mock_item_service):
        mock_item_service.get_all.return_value = []
        pagination = MagicMock()
        item_filter = MagicMock()

        with patch("app.modules.items.routers.log_action"):
            await list_items(pagination, item_filter, mock_item_service)

        mock_item_service.get_all.assert_called_once_with(
            entity_filter=item_filter,
            pagination_params=pagination,
        )

    async def test_returns_result(self, mock_item_service):
        mock_page = MagicMock()
        mock_item_service.get_all.return_value = mock_page
        pagination = MagicMock()
        item_filter = MagicMock()

        with patch("app.modules.items.routers.log_action"):
            result = await list_items(pagination, item_filter, mock_item_service)

        assert result is mock_page


class TestGetItem:
    async def test_returns_item_when_found(self, mock_item_service, sample_item_response, sample_item_id):
        mock_item_service.get_by_id.return_value = sample_item_response

        with patch("app.modules.items.routers.log_action"), patch("app.modules.items.routers.log_entity"):
            result = await get_item(sample_item_id, mock_item_service)

        assert result is sample_item_response

    async def test_raises_when_item_not_found(self, mock_item_service, sample_item_id):
        from app.repositories.exceptions import NotFoundError

        mock_item_service.get_by_id.side_effect = NotFoundError(detail=f"Item {sample_item_id} not found")

        with patch("app.modules.items.routers.log_action"), patch("app.modules.items.routers.log_entity"):
            with pytest.raises(NotFoundError):
                await get_item(sample_item_id, mock_item_service)

    async def test_calls_service_with_item_id(self, mock_item_service, sample_item_response, sample_item_id):
        mock_item_service.get_by_id.return_value = sample_item_response

        with patch("app.modules.items.routers.log_action"), patch("app.modules.items.routers.log_entity"):
            await get_item(sample_item_id, mock_item_service)

        mock_item_service.get_by_id.assert_called_once_with(sample_item_id)


class TestGetItemBySku:
    async def test_returns_item_when_found(self, mock_item_service, sample_item_response):
        mock_item_service.get_by_sku.return_value = sample_item_response

        with patch("app.modules.items.routers.log_action"), patch("app.modules.items.routers.log_entity"):
            result = await get_item_by_sku("TEST-SKU", mock_item_service)

        assert result is sample_item_response

    async def test_calls_service_with_sku(self, mock_item_service, sample_item_response):
        mock_item_service.get_by_sku.return_value = sample_item_response

        with patch("app.modules.items.routers.log_action"), patch("app.modules.items.routers.log_entity"):
            await get_item_by_sku("MY-SKU-001", mock_item_service)

        mock_item_service.get_by_sku.assert_called_once_with("MY-SKU-001")


class TestCreateItem:
    async def test_creates_and_returns_item(self, mock_item_service, sample_item_response):
        mock_item_service.create.return_value = sample_item_response
        create_data = ItemCreate(name="New Item", description="desc")

        with patch("app.modules.items.routers.log_action"), patch("app.modules.items.routers.log_entity"):
            result = await create_item(create_data, mock_item_service)

        assert result is sample_item_response
        mock_item_service.create.assert_called_once_with(create_data)


class TestUpdateItem:
    async def test_updates_and_returns_item(
        self, mock_item_service, sample_item_response, sample_item_id
    ):
        mock_item_service.update.return_value = sample_item_response
        update_data = ItemUpdate(name="Updated")

        with patch("app.modules.items.routers.log_action"), patch("app.modules.items.routers.log_entity"):
            result = await update_item(sample_item_id, update_data, mock_item_service)

        assert result is sample_item_response
        mock_item_service.update.assert_called_once_with(sample_item_id, update_data)


class TestDeleteItem:
    async def test_calls_service_delete(self, mock_item_service, sample_item_id):
        mock_item_service.delete.return_value = None

        with patch("app.modules.items.routers.log_action"), patch("app.modules.items.routers.log_entity"):
            await delete_item(sample_item_id, mock_item_service)

        mock_item_service.delete.assert_called_once_with(sample_item_id)
