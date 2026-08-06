"""Integration tests for central router registration (app/routers.py).

These tests mount the real ``get_app_router()`` and exercise the HTTP routes
end-to-end through FastAPI's TestClient, overriding only the service and auth
dependencies. This verifies prefix/tag wiring and that the mounted routers are
reachable — concerns the old unit tests could not cover by importing handlers
directly.
"""

import uuid
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.teams.dependencies import get_team_service
from app.modules.teams.routers import (
    teams_router,  # noqa: F401  - ensures module import
)
from app.routers import get_app_router
from app.user.auth import require_current_user_id
from app.user.auth.dependencies import get_auth_service
from app.user.auth.permissions import AuthenticatedUser
from app.user.auth.routers import auth_router  # noqa: F401
from app.user.auth.schemas import PasswordResetResponse, SessionResponse
from app.user.dependencies import get_user_service
from app.user.routers import user_router  # noqa: F401


@pytest.fixture
def user_id():
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def team_id():
    return uuid.UUID("99999999-9999-9999-9999-999999999999")


@pytest.fixture
def router_app(user_id, team_id):
    """A minimal FastAPI app mounting the central router with stubbed deps.

    Every auth entry point and service factory is overridden so requests never
    touch the database, yet the full routing → dependency-injection → handler →
    response-serialization pipeline runs for real.
    """
    app = FastAPI()
    app.include_router(get_app_router())

    # --- Auth overrides -------------------------------------------------
    def _user_id():
        return user_id

    def _make_user():
        return SimpleNamespace(
            id=user_id,
            email="test@example.com",
            display_name="Test User",
            email_verified_at=None,
        )

    async def _load_user():
        return _make_user()

    app.dependency_overrides[require_current_user_id] = _user_id
    app.dependency_overrides[AuthenticatedUser.current_user_id] = _user_id
    app.dependency_overrides[AuthenticatedUser.current_user_email] = (
        lambda: "test@example.com"
    )
    app.dependency_overrides[AuthenticatedUser.current_session_id] = (
        lambda: "s_test_session"
    )
    app.dependency_overrides[AuthenticatedUser.get_current_user] = _load_user

    # --- Service overrides ---------------------------------------------
    team_obj = SimpleNamespace(
        id=team_id,
        name="Test Team",
        key="TEST",
        issue_sequence=0,
    )
    team_svc = MagicMock()
    team_svc.get_by_id = AsyncMock(return_value=team_obj)
    team_svc.create = AsyncMock(return_value=team_obj)
    team_svc.update = AsyncMock(return_value=team_obj)
    team_svc.delete = AsyncMock(return_value=None)
    team_svc.get_all_paginated = AsyncMock(
        return_value=SimpleNamespace(
            items=[team_obj],
            total=1,
            page=1,
            size=50,
            pages=1,
        )
    )
    team_svc.get_role_map_for_user = AsyncMock(return_value={team_id: "admin"})
    app.dependency_overrides[get_team_service] = lambda: team_svc

    user_svc = MagicMock()
    user_svc.update = AsyncMock(return_value=_make_user())
    user_svc.delete = AsyncMock(return_value=None)
    app.dependency_overrides[get_user_service] = lambda: user_svc

    # SessionResponse.expires_in computes (expires_at - datetime.now()) where
    # datetime.now() is naive, so the stub must use a naive datetime too.
    expires_at = datetime.now() + timedelta(days=1)
    auth_svc = MagicMock()
    auth_svc.register = AsyncMock(
        return_value=SessionResponse(id="s_new_session", expires_at=expires_at)
    )
    auth_svc.authenticate = AsyncMock(
        return_value=SessionResponse(id="s_login_session", expires_at=expires_at)
    )
    auth_svc.logout = AsyncMock(return_value=None)
    auth_svc.initiate_password_reset = AsyncMock(return_value="pr_token")
    auth_svc.initiate_email_verification = AsyncMock(return_value="ev_token")
    app.dependency_overrides[get_auth_service] = lambda: auth_svc

    yield app, team_svc, user_svc, auth_svc
    app.dependency_overrides.clear()


@pytest.fixture
def router_client(router_app):
    app, _, _, _ = router_app
    with TestClient(app, base_url="http://test") as client:
        yield client


class TestRouterPrefixes:
    """app/routers.py wires each sub-router under its documented prefix."""

    def test_auth_routes_under_auth_prefix(self, router_client):
        """auth_router is mounted at /auth — bare /login must not resolve."""
        assert router_client.post("/login", json={}).status_code == 404
        # /auth/login exists (service is overridden, so it reaches the handler).
        resp = router_client.post(
            "/auth/login", json={"email": "a@b.com", "password": "secret"}
        )
        assert resp.status_code == 200

    def test_user_routes_under_users_prefix(self, router_client):
        assert router_client.get("/me").status_code == 404
        resp = router_client.get("/users/me")
        assert resp.status_code == 200
        assert resp.json()["email"] == "test@example.com"

    def test_teams_router_has_own_prefix(self, router_client):
        # teams_router declares its own /teams prefix.
        resp = router_client.get("/teams")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["name"] == "Test Team"


class TestTeamsRoutePipeline:
    """Full request → response cycle for teams routes through the mounted router."""

    def test_get_team_by_id_serializes_response(self, router_client, team_id):
        resp = router_client.get(f"/teams/{team_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == str(team_id)
        assert body["name"] == "Test Team"
        assert body["key"] == "TEST"
        assert body["issue_sequence"] == 0

    def test_create_team_returns_201(self, router_client, router_app, team_id):
        _, team_svc, _, _ = router_app
        resp = router_client.post("/teams", json={"name": "New Team", "key": "NEW"})
        assert resp.status_code == 201
        assert resp.json()["id"] == str(team_id)
        team_svc.create.assert_awaited_once()

    def test_delete_team_returns_204(self, router_client, router_app, team_id):
        _, team_svc, _, _ = router_app
        resp = router_client.delete(f"/teams/{team_id}")
        assert resp.status_code == 204
        team_svc.delete.assert_awaited_once()

    def test_create_team_rejects_short_key(self, router_client):
        resp = router_client.post("/teams", json={"name": "T", "key": "X"})
        assert resp.status_code == 422


class TestAuthRoutePipeline:
    def test_register_returns_201_and_session(self, router_client, router_app):
        _, _, _, auth_svc = router_app
        resp = router_client.post(
            "/auth/register",
            json={
                "email": "new@example.com",
                "display_name": "New",
                "raw_password": "secret123",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["id"] == "s_new_session"
        auth_svc.register.assert_awaited_once()

    def test_password_reset_is_non_enumerating(self, router_client, router_app):
        """Reset always returns the success response shape regardless of token outcome."""
        _, _, _, auth_svc = router_app
        resp = router_client.post(
            "/auth/password/reset", json={"email": "anyone@example.com"}
        )
        assert resp.status_code == 200
        assert resp.json() == PasswordResetResponse().model_dump(mode="json")
        auth_svc.initiate_password_reset.assert_awaited_once()

    def test_oauth_callback_unknown_provider_redirects(self, router_client):
        resp = router_client.get(
            "/auth/oauth/unknown/callback",
            params={"code": "c", "state": "s"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "unsupported_provider" in resp.headers["location"]


class TestUserRoutePipeline:
    def test_update_me_calls_service(self, router_client, router_app, user_id):
        _, _, user_svc, _ = router_app
        resp = router_client.patch("/users/me", json={"display_name": "Renamed"})
        assert resp.status_code == 200
        # PATCH /me echoes the updated resource.
        assert resp.json()["id"] == str(user_id)
        assert resp.json()["email"] == "test@example.com"
        user_svc.update.assert_awaited_once()
        called_args = user_svc.update.await_args.args
        assert called_args[0] == user_id
        # The body arrives as the partial update model (email dropped, name kept).
        assert called_args[1].display_name == "Renamed"

    def test_delete_me_returns_204(self, router_client, router_app, user_id):
        _, _, user_svc, _ = router_app
        resp = router_client.delete("/users/me")
        assert resp.status_code == 204
        user_svc.delete.assert_awaited_once_with(user_id)


class TestAppRouterAssembly:
    """Structural checks on get_app_router() — covers app/routers.py directly."""

    def test_includes_all_three_routers(self):
        router = get_app_router()

        paths = {route.path for route in router.routes}
        # One representative path per mounted sub-router.
        assert any(p.startswith("/auth") for p in paths)
        assert any(p.startswith("/users") for p in paths)
        assert any(p.startswith("/teams") for p in paths)

    def test_auth_and_users_have_tags(self):
        from app.routers import get_app_router

        tags = set()
        for route in get_app_router().routes:
            tags.update(getattr(route, "tags", []) or [])
        assert "auth" in tags
        assert "users" in tags
        assert "teams" in tags
