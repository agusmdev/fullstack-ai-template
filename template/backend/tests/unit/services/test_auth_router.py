"""Route-level tests for the Auth router.

These hit the mounted auth_router through FastAPI's TestClient (real HTTP,
dependency injection, response serialization, exception→status mapping) instead
of importing the handler functions and invoking them directly.
"""

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.user.auth.dependencies import get_auth_service
from app.user.auth.exceptions import InvalidTokenError, OAuthUserPasswordResetError
from app.user.auth.permissions import AuthenticatedUser
from app.user.auth.routers import auth_router
from app.user.auth.schemas import SessionResponse


@pytest.fixture
def user_id():
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def expires_at():
    # SessionResponse.expires_in uses naive datetime.now(); keep this naive too.
    return datetime.now() + timedelta(days=1)


@pytest.fixture
def session(expires_at):
    return SessionResponse(id="s_test_session", expires_at=expires_at)


@pytest.fixture
def auth_service(session):
    svc = MagicMock()
    svc.authenticate = AsyncMock(return_value=session)
    svc.register = AsyncMock(return_value=session)
    svc.logout = AsyncMock(return_value=None)
    svc.logout_all = AsyncMock(return_value=None)
    svc.initiate_password_reset = AsyncMock(return_value="pr_token")
    svc.reset_password = AsyncMock(return_value=None)
    svc.initiate_email_verification = AsyncMock(return_value="ev_token")
    svc.verify_email = AsyncMock(return_value=None)
    svc.oauth_login = AsyncMock(return_value=session)
    return svc


@pytest.fixture
def client(user_id, auth_service):
    app = FastAPI()
    app.include_router(auth_router)
    app.dependency_overrides[AuthenticatedUser.current_user_id] = lambda: user_id
    app.dependency_overrides[AuthenticatedUser.current_session_id] = (
        lambda: "s_test_session"
    )
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    with TestClient(app, base_url="http://test") as c:
        yield c


class TestLogin:
    def test_returns_session(self, client, auth_service):
        response = client.post(
            "/login", json={"email": "test@example.com", "password": "password123"}
        )

        assert response.status_code == 200
        assert response.json()["id"] == "s_test_session"
        auth_service.authenticate.assert_awaited_once_with(
            email="test@example.com", password="password123"
        )


class TestRegister:
    def test_returns_session_and_201(self, client, auth_service):
        payload = {
            "email": "new@example.com",
            "display_name": "New User",
            "raw_password": "secret123",
        }
        response = client.post("/register", json=payload)

        assert response.status_code == 201
        assert response.json()["id"] == "s_test_session"
        auth_service.register.assert_awaited_once()
        _, kwargs = auth_service.register.await_args
        assert kwargs["new_user"].email == "new@example.com"


class TestLogout:
    def test_logout_invalidates_session(self, client, auth_service):
        response = client.post("/logout")

        assert response.status_code == 200
        auth_service.logout.assert_awaited_once_with("s_test_session")

    def test_logout_all_invalidates_all(self, client, auth_service, user_id):
        response = client.post("/logout/all")

        assert response.status_code == 200
        auth_service.logout_all.assert_awaited_once_with(user_id)


class TestOAuthCallback:
    def test_unknown_provider_redirects_to_error(self, client, auth_service):
        response = client.get(
            "/oauth/unknown/callback",
            params={"code": "auth_code", "state": "st"},
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert "unsupported_provider" in response.headers["location"]
        auth_service.oauth_login.assert_not_awaited()

    def test_known_provider_redirects_with_session(self, client, auth_service):
        response = client.get(
            "/oauth/google/callback",
            params={"code": "auth_code", "state": "st"},
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert "s_test_session" in response.headers["location"]
        auth_service.oauth_login.assert_awaited_once()

    def test_service_error_propagates(self, client, auth_service):
        auth_service.oauth_login.side_effect = RuntimeError("unexpected")

        with pytest.raises(RuntimeError):
            client.get(
                "/oauth/google/callback",
                params={"code": "code", "state": "st"},
                follow_redirects=False,
            )


class TestPasswordReset:
    def test_reset_for_valid_email(self, client, auth_service):
        response = client.post("/password/reset", json={"email": "user@example.com"})

        assert response.status_code == 200
        auth_service.initiate_password_reset.assert_awaited_once_with(
            "user@example.com"
        )

    def test_reset_for_oauth_user_is_non_enumerating(self, client, auth_service):
        """OAuth users get the same success response as anyone else."""
        auth_service.initiate_password_reset.side_effect = OAuthUserPasswordResetError()

        response = client.post("/password/reset", json={"email": "oauth@example.com"})

        assert response.status_code == 200

    def test_reset_when_user_not_found_still_succeeds(self, client, auth_service):
        auth_service.initiate_password_reset.return_value = None

        response = client.post("/password/reset", json={"email": "nope@example.com"})

        assert response.status_code == 200

    def test_confirm_resets_password(self, client, auth_service):
        response = client.post(
            "/password/confirm",
            json={"token": "pr_token", "new_password": "newpass123"},
        )

        assert response.status_code == 200
        auth_service.reset_password.assert_awaited_once_with("pr_token", "newpass123")

    def test_confirm_invalid_token_returns_400(self, client, auth_service):
        auth_service.reset_password.side_effect = InvalidTokenError()

        response = client.post(
            "/password/confirm", json={"token": "invalid", "new_password": "newpass"}
        )

        assert response.status_code == 400


class TestEmailVerification:
    def test_request_verification(self, client, auth_service, user_id):
        response = client.post("/email/verify")

        assert response.status_code == 200
        auth_service.initiate_email_verification.assert_awaited_once_with(user_id)

    def test_confirm_verification(self, client, auth_service):
        response = client.post("/email/verify/confirm", json={"token": "ev_token"})

        assert response.status_code == 200
        auth_service.verify_email.assert_awaited_once_with("ev_token")

    def test_confirm_invalid_token_returns_400(self, client, auth_service):
        auth_service.verify_email.side_effect = InvalidTokenError()

        response = client.post("/email/verify/confirm", json={"token": "invalid"})

        assert response.status_code == 400
