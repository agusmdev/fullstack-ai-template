"""Route-level tests for the Labels router.

Hits the mounted router through FastAPI's TestClient with the service and auth
dependencies overridden — no database touched.
"""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.labels.dependencies import get_label_service
from app.modules.labels.routers import labels_router
from app.repositories.exceptions import NotFoundError
from app.user.auth import require_current_user_id


@pytest.fixture
def user_id():
    return uuid.UUID("87654321-4321-8765-4321-876543218765")


@pytest.fixture
def team_id():
    return uuid.UUID("99999999-9999-9999-9999-999999999999")


@pytest.fixture
def label_id():
    return uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


@pytest.fixture
def label_obj(label_id, team_id):
    return SimpleNamespace(
        id=label_id,
        team_id=team_id,
        name="Bug",
        color="#eb5757",
    )


@pytest.fixture
def service(label_obj):
    svc = MagicMock()
    svc.get_by_id = AsyncMock(return_value=label_obj)
    svc.create = AsyncMock(return_value=label_obj)
    svc.update = AsyncMock(return_value=label_obj)
    svc.delete = AsyncMock(return_value=None)
    svc.get_all_paginated = AsyncMock(
        return_value=SimpleNamespace(
            items=[label_obj], total=1, page=1, size=50, pages=1
        )
    )
    return svc


@pytest.fixture
def client(user_id, service):
    app = FastAPI()
    app.include_router(labels_router)
    app.dependency_overrides[require_current_user_id] = lambda: user_id
    app.dependency_overrides[get_label_service] = lambda: service
    with TestClient(app, base_url="http://test") as c:
        yield c


class TestAuthGuard:
    def test_no_token_rejected(self):
        """Without overriding auth, the router must reject unauthenticated calls.

        The template's HTTPBearer(auto_error=True) returns 403 for a missing
        Authorization header (same behaviour as every other guarded router).
        """
        app = FastAPI()
        app.include_router(labels_router)
        with TestClient(app, base_url="http://test") as c:
            response = c.get("/labels")
        assert response.status_code in (401, 403)


class TestList:
    def test_returns_paginated_labels(self, client):
        response = client.get("/labels")

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["items"][0]["name"] == "Bug"
        assert body["items"][0]["color"] == "#eb5757"

    def test_passes_team_id(self, client, service, team_id):
        client.get("/labels", params={"team_id": str(team_id)})

        _args, kwargs = service.get_all_paginated.await_args
        assert kwargs["team_id"] == team_id


class TestGet:
    def test_returns_label_by_id(self, client, label_id):
        response = client.get(f"/labels/{label_id}")

        assert response.status_code == 200
        assert response.json()["id"] == str(label_id)

    def test_not_found_returns_404(self, client, service, label_id):
        service.get_by_id.side_effect = NotFoundError(detail="not found")

        response = client.get(f"/labels/{label_id}")

        assert response.status_code == 404


class TestCreate:
    def test_creates_and_returns_201(self, client, service, user_id, team_id):
        response = client.post(
            "/labels",
            json={"team_id": str(team_id), "name": "Feature", "color": "#00ff00"},
        )

        assert response.status_code == 201
        _args, kwargs = service.create.await_args
        assert kwargs["user_id"] == user_id

    def test_rejects_missing_name(self, client, team_id):
        response = client.post(
            "/labels", json={"team_id": str(team_id), "color": "#00ff00"}
        )

        assert response.status_code == 422


class TestUpdate:
    def test_updates_label(self, client, service, label_id):
        response = client.patch(f"/labels/{label_id}", json={"name": "Renamed"})

        assert response.status_code == 200
        service.update.assert_awaited_once()


class TestDelete:
    def test_returns_204(self, client, service, label_id, user_id):
        response = client.delete(f"/labels/{label_id}")

        assert response.status_code == 204
        service.delete.assert_awaited_once_with(label_id, user_id=user_id)
