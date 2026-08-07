"""Route-level tests for the Views router.

Hits the mounted router through FastAPI's TestClient with the service and auth
dependencies overridden — no database touched.
"""

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.views.dependencies import get_view_service
from app.modules.views.routers import views_router
from app.repositories.exceptions import NotFoundError
from app.user.auth import require_current_user_id


@pytest.fixture
def user_id():
    return uuid.UUID("87654321-4321-8765-4321-876543218765")


@pytest.fixture
def team_id():
    return uuid.UUID("99999999-9999-9999-9999-999999999999")


@pytest.fixture
def view_id():
    return uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


@pytest.fixture
def view_obj(view_id, team_id, user_id):
    return SimpleNamespace(
        id=view_id,
        owner_id=user_id,
        team_id=team_id,
        name="Urgent bugs",
        filters={"status_id": "st-1", "priority": 0},
        group_by="status",
        order_by="priority",
        description=None,
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        updated_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
    )


@pytest.fixture
def service(view_obj):
    svc = MagicMock()
    svc.get_by_id = AsyncMock(return_value=view_obj)
    svc.create = AsyncMock(return_value=view_obj)
    svc.update = AsyncMock(return_value=view_obj)
    svc.delete = AsyncMock(return_value=None)
    svc.get_all_paginated = AsyncMock(
        return_value=SimpleNamespace(
            items=[view_obj], total=1, page=1, size=50, pages=1
        )
    )
    return svc


@pytest.fixture
def client(user_id, service):
    app = FastAPI()
    app.include_router(views_router)
    app.dependency_overrides[require_current_user_id] = lambda: user_id
    app.dependency_overrides[get_view_service] = lambda: service
    with TestClient(app, base_url="http://test") as c:
        yield c


class TestAuthGuard:
    def test_no_token_rejected(self):
        """Without overriding auth, the router rejects unauthenticated calls (401)."""
        app = FastAPI()
        app.include_router(views_router)
        with TestClient(app, base_url="http://test") as c:
            response = c.get("/views")
        assert response.status_code == 401


class TestList:
    def test_returns_paginated_views(self, client):
        response = client.get("/views")

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["items"][0]["name"] == "Urgent bugs"
        assert body["items"][0]["filters"]["priority"] == 0
        assert body["items"][0]["group_by"] == "status"
        assert body["items"][0]["order_by"] == "priority"

    def test_passes_team_id_and_user_id(self, client, service, user_id, team_id):
        client.get("/views", params={"team_id": str(team_id)})

        _args, kwargs = service.get_all_paginated.await_args
        assert kwargs["user_id"] == user_id
        assert kwargs["team_id"] == team_id


class TestGet:
    def test_returns_view_by_id(self, client, view_id):
        response = client.get(f"/views/{view_id}")

        assert response.status_code == 200
        assert response.json()["id"] == str(view_id)

    def test_not_found_returns_404(self, client, service, view_id):
        service.get_by_id.side_effect = NotFoundError(detail="not found")

        response = client.get(f"/views/{view_id}")

        assert response.status_code == 404


class TestCreate:
    def test_creates_and_returns_201(self, client, service, user_id, team_id):
        response = client.post(
            "/views",
            json={
                "team_id": str(team_id),
                "name": "Urgent bugs",
                "filters": {"status_id": "st-1", "priority": 0},
                "group_by": "status",
                "order_by": "priority",
            },
        )

        assert response.status_code == 201
        _args, kwargs = service.create.await_args
        assert kwargs["user_id"] == user_id

    def test_name_required_empty_rejected(self, client, team_id):
        """An empty name is rejected with 422 (VAL-VIEWS-002)."""
        response = client.post(
            "/views",
            json={"team_id": str(team_id), "name": ""},
        )

        assert response.status_code == 422

    def test_name_required_whitespace_rejected(self, client, team_id):
        """A whitespace-only name is rejected with 422 (VAL-VIEWS-002)."""
        response = client.post(
            "/views",
            json={"team_id": str(team_id), "name": "   "},
        )

        assert response.status_code == 422

    def test_rejects_missing_name(self, client, team_id):
        response = client.post("/views", json={"team_id": str(team_id)})

        assert response.status_code == 422

    def test_rejects_missing_team_id(self, client):
        response = client.post("/views", json={"name": "V"})

        assert response.status_code == 422

    def test_defaults_filters_when_omitted(self, client, service, team_id, view_obj):
        """When filters are omitted, the create schema defaults to an empty dict."""
        service.create = AsyncMock(return_value=view_obj)

        response = client.post(
            "/views", json={"team_id": str(team_id), "name": "All issues"}
        )

        assert response.status_code == 201
        args, _kwargs = service.create.call_args
        assert args[0].filters == {}


class TestUpdate:
    def test_updates_and_returns_view(self, client, service, view_id):
        response = client.patch(f"/views/{view_id}", json={"name": "Renamed"})

        assert response.status_code == 200
        service.update.assert_awaited_once()


class TestDelete:
    def test_returns_204(self, client, service, view_id, user_id):
        response = client.delete(f"/views/{view_id}")

        assert response.status_code == 204
        service.delete.assert_awaited_once_with(view_id, user_id=user_id)
