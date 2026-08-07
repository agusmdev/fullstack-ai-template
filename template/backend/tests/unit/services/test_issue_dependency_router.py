"""Route-level tests for the IssueDependency router.

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

from app.modules.issue_dependencies.dependencies import get_issue_dependency_service
from app.modules.issue_dependencies.routers import issue_dependencies_router
from app.repositories.exceptions import NotFoundError
from app.user.auth import require_current_user_id

NOW = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

A_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
B_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
TEAM_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
def user_id():
    return uuid.UUID("87654321-4321-8765-4321-876543218765")


@pytest.fixture
def dep_id():
    return uuid.UUID("55555555-5555-5555-5555-555555555555")


@pytest.fixture
def dep_obj(dep_id):
    return SimpleNamespace(
        id=dep_id,
        blocker_id=A_ID,
        blocked_id=B_ID,
        relation="blocks",
        # Nested briefs (IssueDependencyResponse.blocker/blocked).
        blocker=SimpleNamespace(
            id=A_ID, identifier="ENG-1", title="A", priority=2,
            status_id=uuid.UUID("44444444-4444-4444-4444-444444444444"),
        ),
        blocked=SimpleNamespace(
            id=B_ID, identifier="ENG-2", title="B", priority=3,
            status_id=uuid.UUID("44444444-4444-4444-4444-444444444444"),
        ),
        created_at=NOW,
        updated_at=NOW,
    )


@pytest.fixture
def service(dep_obj):
    svc = MagicMock()
    svc.get_by_id = AsyncMock(return_value=dep_obj)
    svc.create = AsyncMock(return_value=dep_obj)
    svc.delete = AsyncMock(return_value=None)
    svc.get_all_paginated = AsyncMock(
        return_value=SimpleNamespace(
            items=[dep_obj], total=1, page=1, size=50, pages=1
        )
    )
    return svc


@pytest.fixture
def client(user_id, service):
    app = FastAPI()
    app.include_router(issue_dependencies_router)
    app.dependency_overrides[require_current_user_id] = lambda: user_id
    app.dependency_overrides[get_issue_dependency_service] = lambda: service
    with TestClient(app, base_url="http://test") as c:
        yield c


class TestAuthGuard:
    def test_no_token_rejected(self):
        """Without overriding auth, the router rejects unauthenticated calls."""
        app = FastAPI()
        app.include_router(issue_dependencies_router)
        with TestClient(app, base_url="http://test") as c:
            response = c.get("/issue-dependencies")
        assert response.status_code == 401


class TestList:
    def test_returns_paginated(self, client):
        response = client.get("/issue-dependencies")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1

    def test_passes_issue_id(self, client, service, user_id):
        client.get("/issue-dependencies", params={"issue_id": str(A_ID)})
        _args, kwargs = service.get_all_paginated.await_args
        assert kwargs["issue_id"] == A_ID

    def test_response_includes_blocker_and_blocked_briefs(self, client):
        """The response carries nested blocker/blocked issue briefs so the SPA
        can render reciprocal display without a second fetch (VAL-DEPS-002)."""
        response = client.get("/issue-dependencies")
        item = response.json()["items"][0]
        assert item["blocker"]["identifier"] == "ENG-1"
        assert item["blocked"]["identifier"] == "ENG-2"


class TestCreate:
    def test_creates_and_returns_201(self, client, service, user_id):
        response = client.post(
            "/issue-dependencies",
            json={"blocker_id": str(A_ID), "blocked_id": str(B_ID)},
        )
        assert response.status_code == 201
        _args, kwargs = service.create.await_args
        assert kwargs["user_id"] == user_id

    def test_rejects_missing_blocker(self, client):
        response = client.post(
            "/issue-dependencies", json={"blocked_id": str(B_ID)}
        )
        assert response.status_code == 422

    def test_rejects_missing_blocked(self, client):
        response = client.post(
            "/issue-dependencies", json={"blocker_id": str(A_ID)}
        )
        assert response.status_code == 422


class TestDelete:
    def test_returns_204(self, client, service, dep_id, user_id):
        response = client.delete(f"/issue-dependencies/{dep_id}")
        assert response.status_code == 204
        service.delete.assert_awaited_once_with(dep_id, user_id=user_id)

    def test_not_found_returns_404(self, client, service, dep_id):
        service.delete.side_effect = NotFoundError(detail="not found")
        response = client.delete(f"/issue-dependencies/{dep_id}")
        assert response.status_code == 404
