"""Route-level tests for the Items router.

These hit the mounted items_router through FastAPI's TestClient (real HTTP,
dependency injection, response serialization) instead of importing the handler
functions and invoking them directly. The service and auth dependencies are
overridden so no database is touched.
"""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.items.dependencies import get_item_service
from app.modules.items.routers import items_router
from app.repositories.exceptions import NotFoundError
from app.user.auth import require_current_user_id


@pytest.fixture
def user_id():
    return uuid.UUID("87654321-4321-8765-4321-876543218765")


@pytest.fixture
def owner_id():
    return uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


@pytest.fixture
def item_obj(user_id, owner_id):
    return SimpleNamespace(
        id=user_id, user_id=owner_id, name="Test Item", description="A test item"
    )


@pytest.fixture
def item_service(item_obj, user_id):
    svc = MagicMock()
    svc.get_by_id = AsyncMock(return_value=item_obj)
    svc.get_by_sku = AsyncMock(return_value=item_obj)
    svc.create = AsyncMock(return_value=item_obj)
    svc.update = AsyncMock(return_value=item_obj)
    svc.delete = AsyncMock(return_value=None)
    svc.get_all_paginated = AsyncMock(
        return_value=SimpleNamespace(
            items=[item_obj], total=1, page=1, size=50, pages=1
        )
    )
    return svc


@pytest.fixture
def client(user_id, item_service):
    app = FastAPI()
    app.include_router(items_router)
    app.dependency_overrides[require_current_user_id] = lambda: user_id
    app.dependency_overrides[get_item_service] = lambda: item_service
    with TestClient(app, base_url="http://test") as c:
        yield c


class TestListItems:
    def test_returns_paginated_items(self, client, item_service):
        response = client.get("/items")

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["page"] == 1
        assert len(body["items"]) == 1
        assert body["items"][0]["name"] == "Test Item"
        item_service.get_all_paginated.assert_awaited_once()

    def test_propagates_query_params_to_service(self, client, item_service, user_id):
        client.get("/items", params={"page": "2", "size": "10"})

        # The service received a pagination Params object built from the query.
        _args, kwargs = item_service.get_all_paginated.await_args
        assert kwargs["user_id"] == user_id
        assert kwargs["pagination_params"].page == 2
        assert kwargs["pagination_params"].size == 10


class TestGetItem:
    def test_returns_item_by_id(self, client, user_id):
        response = client.get(f"/items/{user_id}")

        assert response.status_code == 200
        assert response.json()["id"] == str(user_id)

    def test_not_found_returns_404(self, client, item_service, user_id):
        item_service.get_by_id.side_effect = NotFoundError(
            detail=f"Item {user_id} not found"
        )

        response = client.get(f"/items/{user_id}")

        assert response.status_code == 404

    def test_owns_user_id_from_auth(self, client, item_service, user_id):
        client.get(f"/items/{user_id}")

        _args, kwargs = item_service.get_by_id.await_args
        assert kwargs["user_id"] == user_id


class TestGetItemBySku:
    def test_returns_item_by_sku(self, client):
        response = client.get("/items/by-sku/TEST-SKU")

        assert response.status_code == 200
        assert response.json()["name"] == "Test Item"


class TestCreateItem:
    def test_creates_and_returns_201(self, client, item_service, user_id, owner_id):
        response = client.post(
            "/items", json={"name": "New Item", "description": "desc"}
        )

        assert response.status_code == 201
        assert response.json()["id"] == str(user_id)
        _args, kwargs = item_service.create.await_args
        assert kwargs["user_id"] == user_id

    def test_rejects_empty_name(self, client):
        response = client.post("/items", json={"name": "", "description": "d"})

        assert response.status_code == 422


class TestUpdateItem:
    def test_updates_and_returns_item(self, client, item_service, user_id):
        response = client.patch(
            f"/items/{user_id}", json={"name": "Updated", "description": "d"}
        )

        assert response.status_code == 200
        item_service.update.assert_awaited_once()


class TestDeleteItem:
    def test_returns_204(self, client, item_service, user_id):
        response = client.delete(f"/items/{user_id}")

        assert response.status_code == 204
        item_service.delete.assert_awaited_once_with(user_id, user_id=user_id)
