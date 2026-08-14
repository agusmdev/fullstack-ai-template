"""Route-level tests for the User router.

These hit the mounted user_router through FastAPI's TestClient (real HTTP,
dependency injection, response serialization) instead of importing the handler
functions and invoking them directly.
"""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.user.auth.permissions import AuthenticatedUser
from app.user.dependencies import get_user_service
from app.user.routers import user_router


@pytest.fixture
def user_id():
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def user_obj(user_id):
    return SimpleNamespace(
        id=user_id,
        email="test@example.com",
        display_name="Test User",
        email_verified_at=None,
    )


@pytest.fixture
def user_service(user_obj):
    svc = MagicMock()
    svc.update = AsyncMock(return_value=user_obj)
    svc.delete = AsyncMock(return_value=None)
    return svc


@pytest.fixture
def client(user_id, user_obj, user_service):
    app = FastAPI()
    app.include_router(user_router)
    app.dependency_overrides[AuthenticatedUser.current_user_id] = lambda: user_id
    app.dependency_overrides[AuthenticatedUser.current_user_email] = (
        lambda: "test@example.com"
    )
    app.dependency_overrides[AuthenticatedUser.get_current_user] = lambda: user_obj
    app.dependency_overrides[get_user_service] = lambda: user_service
    with TestClient(app, base_url="http://test") as c:
        yield c


class TestGetAuthenticatedUser:
    def test_returns_user_response(self, client, user_obj):
        response = client.get("/me")

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == str(user_obj.id)
        assert body["email"] == user_obj.email
        assert body["display_name"] == user_obj.display_name

    def test_is_email_verified_false_when_unverified(self, client):
        response = client.get("/me")

        assert response.json()["is_email_verified"] is False


class TestUpdateLoggedUser:
    def test_calls_service_update(self, client, user_service, user_id):
        response = client.patch("/me", json={"display_name": "New Name"})

        assert response.status_code == 200
        user_service.update.assert_awaited_once()
        args, _ = user_service.update.await_args
        assert args[0] == user_id
        assert args[1].display_name == "New Name"

    def test_returns_updated_user(self, client, user_obj):
        response = client.patch("/me", json={"display_name": "X"})

        # update_logged_user echoes the updated resource (mirrors items PATCH).
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == str(user_obj.id)
        assert body["email"] == user_obj.email


class TestDeleteUser:
    def test_calls_service_delete(self, client, user_service, user_id):
        response = client.delete("/me")

        assert response.status_code == 204
        user_service.delete.assert_awaited_once_with(user_id)
