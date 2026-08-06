"""Route-level tests for the Issues router.

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

from app.modules.issues.dependencies import get_issue_service
from app.modules.issues.routers import issues_router
from app.repositories.exceptions import NotFoundError
from app.user.auth import require_current_user_id

NOW = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def user_id():
    return uuid.UUID("87654321-4321-8765-4321-876543218765")


@pytest.fixture
def team_id():
    return uuid.UUID("99999999-9999-9999-9999-999999999999")


@pytest.fixture
def status_id():
    return uuid.UUID("44444444-4444-4444-4444-444444444444")


@pytest.fixture
def label_id():
    return uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


@pytest.fixture
def issue_id():
    return uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


@pytest.fixture
def issue_obj(issue_id, team_id, status_id, user_id):
    return SimpleNamespace(
        id=issue_id,
        team_id=team_id,
        identifier="ENG-1",
        title="Test issue",
        description="A description",
        status_id=status_id,
        priority=4,
        assignee_id=None,
        creator_id=user_id,
        project_id=None,
        cycle_id=None,
        parent_id=None,
        sort_order=0.0,
        estimate=None,
        due_date=None,
        labels=[],
        created_at=NOW,
        updated_at=NOW,
    )


@pytest.fixture
def service(issue_obj):
    svc = MagicMock()
    svc.get_by_id = AsyncMock(return_value=issue_obj)
    svc.create = AsyncMock(return_value=issue_obj)
    svc.update = AsyncMock(return_value=issue_obj)
    svc.delete = AsyncMock(return_value=None)
    svc.add_label = AsyncMock(return_value=issue_obj)
    svc.remove_label = AsyncMock(return_value=issue_obj)
    svc.get_all_paginated = AsyncMock(
        return_value=SimpleNamespace(
            items=[issue_obj], total=1, page=1, size=50, pages=1
        )
    )
    return svc


@pytest.fixture
def client(user_id, service):
    app = FastAPI()
    app.include_router(issues_router)
    app.dependency_overrides[require_current_user_id] = lambda: user_id
    app.dependency_overrides[get_issue_service] = lambda: service
    with TestClient(app, base_url="http://test") as c:
        yield c


class TestAuthGuard:
    def test_no_token_rejected(self):
        """Without overriding auth, the router must reject unauthenticated calls."""
        app = FastAPI()
        app.include_router(issues_router)
        with TestClient(app, base_url="http://test") as c:
            response = c.get("/issues")
        assert response.status_code in (401, 403)


class TestList:
    def test_returns_paginated_issues(self, client):
        response = client.get("/issues")

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["items"][0]["title"] == "Test issue"
        assert body["items"][0]["identifier"] == "ENG-1"

    def test_passes_team_id(self, client, service, team_id):
        client.get("/issues", params={"team_id": str(team_id)})

        _args, kwargs = service.get_all_paginated.await_args
        assert kwargs["team_id"] == team_id

    def test_passes_label_id(self, client, service, label_id):
        client.get("/issues", params={"label_id": str(label_id)})

        _args, kwargs = service.get_all_paginated.await_args
        assert kwargs["label_id"] == label_id

    def test_filter_params_accepted(self, client, service, status_id):
        """Status, priority, assignee filters are accepted as query params."""
        response = client.get(
            "/issues",
            params={
                "status_id": str(status_id),
                "priority": 0,
                "search": "bug",
                "order_by": "-created_at",
            },
        )
        assert response.status_code == 200


class TestGet:
    def test_returns_issue_by_id(self, client, issue_id):
        response = client.get(f"/issues/{issue_id}")

        assert response.status_code == 200
        assert response.json()["id"] == str(issue_id)

    def test_not_found_returns_404(self, client, service, issue_id):
        service.get_by_id.side_effect = NotFoundError(detail="not found")

        response = client.get(f"/issues/{issue_id}")

        assert response.status_code == 404


class TestCreate:
    def test_creates_and_returns_201(self, client, service, user_id, team_id):
        response = client.post(
            "/issues",
            json={"team_id": str(team_id), "title": "New issue"},
        )

        assert response.status_code == 201
        _args, kwargs = service.create.await_args
        assert kwargs["user_id"] == user_id

    def test_rejects_missing_title(self, client, team_id):
        response = client.post(
            "/issues", json={"team_id": str(team_id)}
        )

        assert response.status_code == 422

    def test_rejects_missing_team_id(self, client):
        response = client.post("/issues", json={"title": "No team"})

        assert response.status_code == 422

    def test_whitespace_title_rejected(self, client, team_id):
        """Whitespace-only title is treated as empty (min_length=1)."""
        response = client.post(
            "/issues", json={"team_id": str(team_id), "title": "   "}
        )

        assert response.status_code == 422

    def test_priority_range_validated(self, client, team_id):
        """Priority outside 0-4 is rejected."""
        response = client.post(
            "/issues",
            json={"team_id": str(team_id), "title": "X", "priority": 5},
        )

        assert response.status_code == 422


class TestUpdate:
    def test_updates_issue(self, client, service, issue_id):
        response = client.patch(
            f"/issues/{issue_id}", json={"title": "Updated title"}
        )

        assert response.status_code == 200
        service.update.assert_awaited_once()


class TestDelete:
    def test_returns_204(self, client, service, issue_id, user_id):
        response = client.delete(f"/issues/{issue_id}")

        assert response.status_code == 204
        service.delete.assert_awaited_once_with(issue_id, user_id=user_id)


class TestLabelsSubResource:
    def test_add_label(self, client, service, issue_id, label_id, user_id):
        response = client.post(f"/issues/{issue_id}/labels/{label_id}")

        assert response.status_code == 200
        service.add_label.assert_awaited_once_with(
            issue_id, label_id, user_id=user_id
        )

    def test_remove_label(self, client, service, issue_id, label_id, user_id):
        response = client.delete(f"/issues/{issue_id}/labels/{label_id}")

        assert response.status_code == 200
        service.remove_label.assert_awaited_once_with(
            issue_id, label_id, user_id=user_id
        )
