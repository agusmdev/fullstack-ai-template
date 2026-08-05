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
    svc.get_all_paginated = AsyncMock()
    svc.create = AsyncMock()
    svc.update = AsyncMock()
    svc.delete = AsyncMock()
    svc.get_by_sku = AsyncMock()
    return svc


@pytest.fixture
def sample_item_id():
    return uuid.UUID("87654321-4321-8765-4321-876543218765")


@pytest.fixture
def sample_item_owner_id():
    return uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


@pytest.fixture
def sample_item_response(sample_item_id, sample_item_owner_id):
    item = MagicMock()
    item.id = sample_item_id
    item.user_id = sample_item_owner_id
    item.name = "Test Item"
    item.description = "A test item"
    return item


@pytest.fixture
def sample_page(sample_item_response):
    """A page-like object whose items/metadata the router can validate."""
    page = MagicMock()
    page.items = [sample_item_response]
    page.total = 1
    page.page = 1
    page.size = 50
    page.pages = 1
    return page


class TestListItems:
    async def test_calls_service_get_all_paginated(
        self, mock_item_service, sample_page
    ):
        mock_item_service.get_all_paginated.return_value = sample_page
        pagination = MagicMock()
        item_filter = MagicMock()
        user_id = uuid.uuid4()

        with patch("app.modules.items.routers.log_action"):
            await list_items(pagination, item_filter, user_id, mock_item_service)

        mock_item_service.get_all_paginated.assert_called_once_with(
            pagination_params=pagination,
            entity_filter=item_filter,
            user_id=user_id,
        )

    async def test_returns_result(self, mock_item_service, sample_page, sample_item_id):
        mock_item_service.get_all_paginated.return_value = sample_page
        pagination = MagicMock()
        item_filter = MagicMock()
        user_id = uuid.uuid4()

        with patch("app.modules.items.routers.log_action"):
            result = await list_items(
                pagination, item_filter, user_id, mock_item_service
            )

        assert result.total == 1
        assert result.page == 1
        assert result.size == 50
        assert len(result.items) == 1
        assert isinstance(result.items[0], ItemResponse)
        assert result.items[0].id == sample_item_id


class TestGetItem:
    async def test_returns_item_when_found(
        self, mock_item_service, sample_item_response, sample_item_id
    ):
        mock_item_service.get_by_id.return_value = sample_item_response
        user_id = uuid.uuid4()

        with patch("app.modules.items.routers.log_action"):
            result = await get_item(sample_item_id, user_id, mock_item_service)

        assert isinstance(result, ItemResponse)
        assert result.id == sample_item_id

    async def test_raises_when_item_not_found(self, mock_item_service, sample_item_id):
        from app.repositories.exceptions import NotFoundError

        mock_item_service.get_by_id.side_effect = NotFoundError(
            detail=f"Item {sample_item_id} not found"
        )
        user_id = uuid.uuid4()

        with patch("app.modules.items.routers.log_action"):
            with pytest.raises(NotFoundError):
                await get_item(sample_item_id, user_id, mock_item_service)

    async def test_calls_service_with_item_id(
        self, mock_item_service, sample_item_response, sample_item_id
    ):
        mock_item_service.get_by_id.return_value = sample_item_response
        user_id = uuid.uuid4()

        with patch("app.modules.items.routers.log_action"):
            await get_item(sample_item_id, user_id, mock_item_service)

        mock_item_service.get_by_id.assert_called_once_with(
            sample_item_id, user_id=user_id
        )


class TestGetItemBySku:
    async def test_returns_item_when_found(
        self, mock_item_service, sample_item_response
    ):
        mock_item_service.get_by_sku.return_value = sample_item_response
        user_id = uuid.uuid4()

        with (
            patch("app.modules.items.routers.log_action"),
            patch("app.modules.items.routers.log_entity"),
        ):
            result = await get_item_by_sku("TEST-SKU", user_id, mock_item_service)

        assert isinstance(result, ItemResponse)
        assert result.id == sample_item_response.id

    async def test_calls_service_with_sku(
        self, mock_item_service, sample_item_response
    ):
        mock_item_service.get_by_sku.return_value = sample_item_response
        user_id = uuid.uuid4()

        with (
            patch("app.modules.items.routers.log_action"),
            patch("app.modules.items.routers.log_entity"),
        ):
            await get_item_by_sku("MY-SKU-001", user_id, mock_item_service)

        mock_item_service.get_by_sku.assert_called_once_with(
            "MY-SKU-001", user_id=user_id
        )


class TestCreateItem:
    async def test_creates_and_returns_item(
        self, mock_item_service, sample_item_response
    ):
        mock_item_service.create.return_value = sample_item_response
        create_data = ItemCreate(name="New Item", description="desc")
        user_id = uuid.uuid4()

        with (
            patch("app.modules.items.routers.log_action"),
            patch("app.modules.items.routers.log_entity"),
        ):
            result = await create_item(create_data, user_id, mock_item_service)

        assert isinstance(result, ItemResponse)
        assert result.id == sample_item_response.id
        mock_item_service.create.assert_called_once_with(create_data, user_id=user_id)


class TestUpdateItem:
    async def test_updates_and_returns_item(
        self, mock_item_service, sample_item_response, sample_item_id
    ):
        mock_item_service.update.return_value = sample_item_response
        update_data = ItemUpdate(name="Updated")
        user_id = uuid.uuid4()

        with (
            patch("app.modules.items.routers.log_action"),
            patch("app.modules.items.routers.log_entity"),
        ):
            result = await update_item(
                sample_item_id, update_data, user_id, mock_item_service
            )

        assert isinstance(result, ItemResponse)
        assert result.id == sample_item_id
        mock_item_service.update.assert_called_once_with(
            sample_item_id, update_data, user_id=user_id
        )


class TestDeleteItem:
    async def test_calls_service_delete(self, mock_item_service, sample_item_id):
        mock_item_service.delete.return_value = None
        user_id = uuid.uuid4()

        with (
            patch("app.modules.items.routers.log_action"),
            patch("app.modules.items.routers.log_entity"),
        ):
            await delete_item(sample_item_id, user_id, mock_item_service)

        mock_item_service.delete.assert_called_once_with(
            sample_item_id, user_id=user_id
        )
