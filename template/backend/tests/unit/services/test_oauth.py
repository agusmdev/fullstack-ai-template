"""Tests for OAuth flow: GoogleOAuth.callback(), AuthService.oauth_login(), and oauth_callback router."""

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.user.auth.exceptions import UnsupportedOAuthProviderError
from app.user.auth.routers import oauth_callback
from app.user.auth.schemas import OAuthCallback, OAuthUser, SessionResponse
from app.user.auth.service import GoogleOAuth


# ---------------------------------------------------------------------------
# GoogleOAuth.callback()
# ---------------------------------------------------------------------------


class TestGoogleOAuthCallback:
    def _make_callback(self) -> OAuthCallback:
        return OAuthCallback(code="auth_code_123", state="state_abc")

    @patch("app.user.auth.service.OAuth2Session")
    def test_returns_oauth_user_on_success(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.fetch_token.return_value = {"access_token": "tok_xyz"}
        mock_session.get.return_value.json.return_value = {
            "email": "user@example.com",
            "name": "Test User",
        }

        result = GoogleOAuth().callback(self._make_callback())

        assert result.token == "tok_xyz"
        assert result.email == "user@example.com"
        assert result.display_name == "Test User"

    @patch("app.user.auth.service.OAuth2Session")
    def test_passes_code_and_state_to_oauth2session(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.fetch_token.return_value = {"access_token": "tok"}
        mock_session.get.return_value.json.return_value = {
            "email": "a@b.com",
            "name": "A",
        }

        GoogleOAuth().callback(self._make_callback())

        call_kwargs = mock_session_cls.call_args.kwargs
        assert call_kwargs["state"] == "state_abc"

    @patch("app.user.auth.service.OAuth2Session")
    def test_missing_display_name_raises_validation_error(self, mock_session_cls):
        """OAuthUser.display_name is required (str); missing 'name' from Google raises."""
        from pydantic import ValidationError

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.fetch_token.return_value = {"access_token": "tok"}
        mock_session.get.return_value.json.return_value = {
            "email": "user@example.com",
            # "name" intentionally absent — Google may omit this field
        }

        with pytest.raises(ValidationError):
            GoogleOAuth().callback(self._make_callback())


# ---------------------------------------------------------------------------
# AuthService.oauth_login()
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_session_response():
    return SessionResponse(
        id="s_test_session",
        expires_at=datetime.now() + timedelta(days=365),
    )


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
    return user


@pytest.fixture
def auth_service_with_mocks(mock_user, mock_session_response):
    """AuthService with mocked repos and user_service."""
    from app.user.auth.service import AuthService

    user_service = MagicMock()
    user_service.find_or_create = AsyncMock(return_value=mock_user)

    repo = MagicMock()
    repo.create = AsyncMock(
        return_value=MagicMock(
            id=mock_session_response.id,
            expires_at=mock_session_response.expires_at,
        )
    )

    service = AuthService(
        user_service=user_service,
        repo=repo,
        password_reset_repo=MagicMock(),
        email_verification_repo=MagicMock(),
    )
    return service


class TestAuthServiceOAuthLogin:
    async def test_raises_for_unsupported_provider(self, auth_service_with_mocks):
        callback = OAuthCallback(code="code", state="state")
        with pytest.raises(UnsupportedOAuthProviderError):
            await auth_service_with_mocks.oauth_login("github", callback)

    async def test_calls_provider_callback_and_creates_session(
        self, auth_service_with_mocks, mock_user
    ):
        mock_provider = MagicMock()
        mock_provider.callback.return_value = OAuthUser(
            token="tok", email="u@example.com", display_name="U"
        )
        auth_service_with_mocks.providers["google"] = mock_provider

        callback = OAuthCallback(code="code", state="state")
        result = await auth_service_with_mocks.oauth_login("google", callback)

        mock_provider.callback.assert_called_once_with(callback)
        auth_service_with_mocks.user_service.find_or_create.assert_awaited_once()
        assert result.id == "s_test_session"

    async def test_find_or_create_called_with_email(
        self, auth_service_with_mocks
    ):
        mock_provider = MagicMock()
        mock_provider.callback.return_value = OAuthUser(
            token="tok", email="hello@example.com", display_name="Hello"
        )
        auth_service_with_mocks.providers["google"] = mock_provider

        callback = OAuthCallback(code="code", state="state")
        await auth_service_with_mocks.oauth_login("google", callback)

        call_args = auth_service_with_mocks.user_service.find_or_create.call_args
        assert call_args.args[0] == "email"
        assert call_args.args[1] == "hello@example.com"


# ---------------------------------------------------------------------------
# oauth_callback router endpoint
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_auth_service_for_router(mock_session_response):
    svc = MagicMock()
    svc.oauth_login = AsyncMock(return_value=mock_session_response)
    return svc


class TestOAuthCallbackRouter:
    async def test_redirects_to_frontend_on_success(
        self, mock_auth_service_for_router
    ):
        callback = OAuthCallback(code="code", state="state")
        response = await oauth_callback(
            provider="google",
            auth_service=mock_auth_service_for_router,
            callback=callback,
        )

        assert response.status_code == 302
        assert "session=" in response.headers["location"]

    async def test_redirects_to_error_on_unsupported_provider(
        self, mock_auth_service_for_router
    ):
        mock_auth_service_for_router.oauth_login.side_effect = UnsupportedOAuthProviderError()
        callback = OAuthCallback(code="code", state="state")

        response = await oauth_callback(
            provider="unsupported",
            auth_service=mock_auth_service_for_router,
            callback=callback,
        )

        assert response.status_code == 302
        assert "unsupported_provider" in response.headers["location"]

    async def test_redirects_to_error_on_generic_exception(
        self, mock_auth_service_for_router
    ):
        mock_auth_service_for_router.oauth_login.side_effect = RuntimeError("network error")
        callback = OAuthCallback(code="code", state="state")

        response = await oauth_callback(
            provider="google",
            auth_service=mock_auth_service_for_router,
            callback=callback,
        )

        assert response.status_code == 302
        assert "oauth_login_failed" in response.headers["location"]
