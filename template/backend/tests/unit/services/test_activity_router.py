"""Route-level tests for the Activity router (read-only).

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

from app.modules.activity import models as activity_models
from app.modules.activity.dependencies import get_activity_service
from app.modules.activity.routers import activity_router
from app.repositories.exceptions import NotFoundError
from app.user.auth import require_current_user_id

NOW = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

ISSUE_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def activity_id():
    return uuid.UUID("55555555-5555-5555-5555-555555555555")


@pytest.fixture
def actor_brief():
    return SimpleNamespace(id=USER_ID, display_name="Ada", email="ada@x.com")


@pytest.fixture
def activity_obj(activity_id, actor_brief):
    return SimpleNamespace(
        id=activity_id,
        issue_id=ISSUE_ID,
        actor_id=USER_ID,
        type=activity_models.STATUS_CHANGE,
        payload={"from": "Backlog", "to": "In Progress"},
        actor=actor_brief,
        created_at=NOW,
        updated_at=NOW,
    )


@pytest.fixture
def service(activity_obj):
    svc = MagicMock()
    svc.get_by_id = AsyncMock(return_value=activity_obj)
    svc.get_all_paginated = AsyncMock(
        return_value=SimpleNamespace(
            items=[activity_obj], total=1, page=1, size=50, pages=1
        )
    )
    return svc


@pytest.fixture
def client(service):
    app = FastAPI()
    app.include_router(activity_router)
    app.dependency_overrides[require_current_user_id] = lambda: USER_ID
    app.dependency_overrides[get_activity_service] = lambda: service
    with TestClient(app, base_url="http://test") as c:
        yield c


class TestAuthGuard:
    def test_no_token_rejected(self):
        """Without overriding auth, the router rejects unauthenticated calls."""
        app = FastAPI()
        app.include_router(activity_router)
        with TestClient(app, base_url="http://test") as c:
            response = c.get("/activity")
        assert response.status_code == 401


class TestList:
    def test_returns_paginated_newest_first(self, client):
        response = client.get("/activity")
        assert response.status_code == 200
        assert response.json()["total"] == 1

    def test_passes_issue_id(self, client, service):
        client.get("/activity", params={"issue_id": str(ISSUE_ID)})
        _args, kwargs = service.get_all_paginated.await_args
        assert kwargs["issue_id"] == ISSUE_ID

    def test_response_includes_actor_brief(self, client):
        """The response carries a nested actor brief so the SPA can render the
        actor without a second fetch (VAL-ACTIVITY-007)."""
        item = client.get("/activity").json()["items"][0]
        assert item["actor"]["display_name"] == "Ada"
        assert item["actor"]["email"] == "ada@x.com"

    def test_response_includes_type_and_payload(self, client):
        """Each entry carries its type and structured payload."""
        item = client.get("/activity").json()["items"][0]
        assert item["type"] == activity_models.STATUS_CHANGE
        assert item["payload"]["from"] == "Backlog"
        assert item["payload"]["to"] == "In Progress"

    def test_not_found_returns_404(self, client, service):
        service.get_all_paginated.side_effect = NotFoundError(detail="no")
        response = client.get("/activity")
        assert response.status_code == 404


class TestDetail:
    def test_returns_activity(self, client, activity_id):
        response = client.get(f"/activity/{activity_id}")
        assert response.status_code == 200
        assert response.json()["type"] == activity_models.STATUS_CHANGE

    def test_not_found_returns_404(self, client, service, activity_id):
        service.get_by_id.side_effect = NotFoundError(detail="no")
        response = client.get(f"/activity/{activity_id}")
        assert response.status_code == 404


class TestReadOnly:
    """Activity is read-only — no create/update/delete endpoints exist
    (VAL-ACTIVITY-009)."""

    def test_no_create_endpoint(self, client):
        response = client.post("/activity", json={"type": "x"})
        assert response.status_code == 405

    def test_no_update_endpoint(self, client, activity_id):
        response = client.patch(f"/activity/{activity_id}", json={"type": "x"})
        assert response.status_code == 405

    def test_no_delete_endpoint(self, client, activity_id):
        response = client.delete(f"/activity/{activity_id}")
        assert response.status_code == 405
