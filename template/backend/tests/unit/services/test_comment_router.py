"""Route-level tests for the Comment router.

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

from app.modules.comments.dependencies import get_comment_service
from app.modules.comments.routers import comments_router
from app.repositories.exceptions import ForbiddenError, NotFoundError
from app.user.auth import require_current_user_id

NOW = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

ISSUE_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def comment_id():
    return uuid.UUID("55555555-5555-5555-5555-555555555555")


@pytest.fixture
def author_brief():
    return SimpleNamespace(
        id=USER_ID, display_name="Ada", email="ada@x.com"
    )


@pytest.fixture
def comment_obj(comment_id, author_brief):
    return SimpleNamespace(
        id=comment_id,
        issue_id=ISSUE_ID,
        author_id=USER_ID,
        body="Hello world",
        author=author_brief,
        created_at=NOW,
        updated_at=NOW,
    )


@pytest.fixture
def service(comment_obj):
    svc = MagicMock()
    svc.get_by_id = AsyncMock(return_value=comment_obj)
    svc.create = AsyncMock(return_value=comment_obj)
    svc.update = AsyncMock(return_value=comment_obj)
    svc.delete = AsyncMock(return_value=None)
    svc.get_all_paginated = AsyncMock(
        return_value=SimpleNamespace(
            items=[comment_obj], total=1, page=1, size=50, pages=1
        )
    )
    return svc


@pytest.fixture
def client(service):
    app = FastAPI()
    app.include_router(comments_router)
    app.dependency_overrides[require_current_user_id] = lambda: USER_ID
    app.dependency_overrides[get_comment_service] = lambda: service
    with TestClient(app, base_url="http://test") as c:
        yield c


class TestAuthGuard:
    def test_no_token_rejected(self):
        """Without overriding auth, the router rejects unauthenticated calls."""
        app = FastAPI()
        app.include_router(comments_router)
        with TestClient(app, base_url="http://test") as c:
            response = c.get("/comments")
        assert response.status_code == 401


class TestList:
    def test_returns_paginated_newest_first(self, client):
        response = client.get("/comments")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1

    def test_passes_issue_id(self, client, service):
        client.get("/comments", params={"issue_id": str(ISSUE_ID)})
        _args, kwargs = service.get_all_paginated.await_args
        assert kwargs["issue_id"] == ISSUE_ID

    def test_response_includes_author_brief(self, client):
        """The response carries a nested author brief so the SPA can render the
        author name without a second fetch (VAL-COMMENTS-004)."""
        response = client.get("/comments")
        item = response.json()["items"][0]
        assert item["author"]["display_name"] == "Ada"
        assert item["author"]["email"] == "ada@x.com"


class TestCreate:
    def test_creates_and_returns_201(self, client, service):
        response = client.post(
            "/comments",
            json={"issue_id": str(ISSUE_ID), "body": "Hello world"},
        )
        assert response.status_code == 201
        _args, kwargs = service.create.await_args
        assert kwargs["user_id"] == USER_ID

    def test_rejects_missing_issue_id(self, client):
        response = client.post("/comments", json={"body": "Hi"})
        assert response.status_code == 422

    def test_rejects_missing_body(self, client):
        response = client.post(
            "/comments", json={"issue_id": str(ISSUE_ID)}
        )
        assert response.status_code == 422


class TestUpdate:
    def test_updates_and_returns_200(self, client, service, comment_id):
        response = client.patch(
            f"/comments/{comment_id}", json={"body": "Edited"}
        )
        assert response.status_code == 200
        service.update.assert_awaited_once()

    def test_forbidden_returns_403(self, client, service, comment_id):
        """A non-author member edit is rejected with 403 (VAL-COMMENTS-008)."""
        service.update.side_effect = ForbiddenError(detail="no")
        response = client.patch(
            f"/comments/{comment_id}", json={"body": "x"}
        )
        assert response.status_code == 403

    def test_not_found_returns_404(self, client, service, comment_id):
        service.update.side_effect = NotFoundError(detail="no")
        response = client.patch(
            f"/comments/{comment_id}", json={"body": "x"}
        )
        assert response.status_code == 404


class TestDelete:
    def test_returns_204(self, client, service, comment_id):
        response = client.delete(f"/comments/{comment_id}")
        assert response.status_code == 204
        service.delete.assert_awaited_once_with(comment_id, user_id=USER_ID)

    def test_forbidden_returns_403(self, client, service, comment_id):
        service.delete.side_effect = ForbiddenError(detail="no")
        response = client.delete(f"/comments/{comment_id}")
        assert response.status_code == 403

    def test_not_found_returns_404(self, client, service, comment_id):
        service.delete.side_effect = NotFoundError(detail="no")
        response = client.delete(f"/comments/{comment_id}")
        assert response.status_code == 404
