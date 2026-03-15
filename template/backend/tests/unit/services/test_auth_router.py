"""Tests for Auth router endpoint functions."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.security import HTTPAuthorizationCredentials

from app.user.auth.exceptions import InvalidTokenError, OAuthUserPasswordResetError
from app.user.auth.routers import (
    confirm_email_verification,
    confirm_password_reset,
    login_user,
    logout_all_devices,
    logout_user,
    oauth_callback,
    register_user,
    request_email_verification,
    request_password_reset,
)
from app.user.auth.schemas import (
    EmailVerificationConfirm,
    LogoutResponse,
    OAuthCallback,
    PasswordResetConfirm,
    PasswordResetRequest,
    SessionResponse,
)
from app.user.schemas import UserRegister


@pytest.fixture
def mock_auth_service():
    svc = MagicMock()
    svc.authenticate = AsyncMock()
    svc.register = AsyncMock()
    svc.logout = AsyncMock()
    svc.logout_all = AsyncMock()
    svc.initiate_password_reset = AsyncMock()
    svc.reset_password = AsyncMock()
    svc.initiate_email_verification = AsyncMock()
    svc.verify_email = AsyncMock()
    return svc


@pytest.fixture
def sample_session_response():
    from datetime import datetime, timedelta

    return SessionResponse(
        id="s_test_session_id",
        expires_at=datetime.now() + timedelta(days=365),
    )


@pytest.fixture
def sample_user_id():
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


class TestLoginUser:
    async def test_calls_authenticate_and_returns_session(
        self, mock_auth_service, sample_session_response
    ):
        mock_auth_service.authenticate.return_value = sample_session_response

        result = await login_user(
            email="test@example.com",
            password="password123",
            auth_service=mock_auth_service,
        )

        mock_auth_service.authenticate.assert_called_once_with(
            email="test@example.com", password="password123"
        )
        assert result == sample_session_response


class TestRegisterUser:
    async def test_calls_register_and_returns_session(
        self, mock_auth_service, sample_session_response
    ):
        mock_auth_service.register.return_value = sample_session_response
        user = UserRegister(
            email="new@example.com", display_name="New User", raw_password="secret123"
        )

        result = await register_user(user=user, auth_service=mock_auth_service)

        mock_auth_service.register.assert_called_once_with(new_user=user)
        assert result == sample_session_response


class TestLogoutUser:
    async def test_calls_logout_and_returns_response(self, mock_auth_service):
        result = await logout_user(
            session_id="s_session_id", auth_service=mock_auth_service
        )

        mock_auth_service.logout.assert_called_once_with("s_session_id")
        assert isinstance(result, LogoutResponse)


class TestLogoutAllDevices:
    async def test_calls_logout_all_and_returns_response(
        self, mock_auth_service, sample_user_id
    ):
        result = await logout_all_devices(
            user_id=sample_user_id, auth_service=mock_auth_service
        )

        mock_auth_service.logout_all.assert_called_once_with(sample_user_id)
        assert isinstance(result, LogoutResponse)


class TestOAuthCallback:
    async def test_redirects_to_error_on_unknown_provider(self, mock_auth_service):
        """Unsupported providers are rejected before the service layer is called."""
        callback = OAuthCallback(code="auth_code", state="st")

        result = await oauth_callback(
            provider="unknown_provider",
            auth_service=mock_auth_service,
            callback=callback,
        )

        mock_auth_service.oauth_login.assert_not_called()
        assert result.status_code == 302
        assert "unsupported_provider" in str(result.headers["location"])

    async def test_redirects_to_frontend_on_success(self, mock_auth_service, sample_session_response):
        """Known provider triggers oauth_login and redirects to frontend."""
        mock_auth_service.oauth_login = AsyncMock(return_value=sample_session_response)
        callback = OAuthCallback(code="auth_code", state="st")

        result = await oauth_callback(
            provider="google",
            auth_service=mock_auth_service,
            callback=callback,
        )

        mock_auth_service.oauth_login.assert_called_once_with(
            provider_name="google", payload=callback
        )
        assert result.status_code == 302
        assert sample_session_response.id in str(result.headers["location"])

    async def test_unexpected_exceptions_propagate(self, mock_auth_service):
        """Unexpected service errors propagate to middleware for structured logging."""
        mock_auth_service.oauth_login.side_effect = RuntimeError("unexpected")
        callback = OAuthCallback(code="code", state="st")

        with pytest.raises(RuntimeError):
            await oauth_callback(
                provider="google",
                auth_service=mock_auth_service,
                callback=callback,
            )


class TestRequestPasswordReset:
    async def test_returns_success_for_valid_email(self, mock_auth_service):
        mock_auth_service.initiate_password_reset.return_value = "pr_token"
        request = PasswordResetRequest(email="user@example.com")

        result = await request_password_reset(
            request=request, auth_service=mock_auth_service
        )

        assert result is not None

    async def test_returns_success_for_oauth_user(self, mock_auth_service):
        mock_auth_service.initiate_password_reset.side_effect = OAuthUserPasswordResetError()
        request = PasswordResetRequest(email="oauth@example.com")

        # Should not raise — returns success to prevent enumeration
        result = await request_password_reset(
            request=request, auth_service=mock_auth_service
        )

        assert result is not None

    async def test_returns_success_when_user_not_found(self, mock_auth_service):
        mock_auth_service.initiate_password_reset.return_value = None
        request = PasswordResetRequest(email="notfound@example.com")

        result = await request_password_reset(
            request=request, auth_service=mock_auth_service
        )

        assert result is not None


class TestConfirmPasswordReset:
    async def test_calls_reset_password(self, mock_auth_service):
        request = PasswordResetConfirm(token="pr_token", new_password="newpass123")

        await confirm_password_reset(request=request, auth_service=mock_auth_service)

        mock_auth_service.reset_password.assert_called_once_with(
            "pr_token", "newpass123"
        )

    async def test_raises_on_invalid_token(self, mock_auth_service):
        mock_auth_service.reset_password.side_effect = InvalidTokenError()
        request = PasswordResetConfirm(token="invalid", new_password="newpass")

        with pytest.raises(InvalidTokenError):
            await confirm_password_reset(request=request, auth_service=mock_auth_service)


class TestRequestEmailVerification:
    async def test_calls_initiate_email_verification(
        self, mock_auth_service, sample_user_id
    ):
        mock_auth_service.initiate_email_verification.return_value = "ev_token"

        await request_email_verification(
            user_id=sample_user_id, auth_service=mock_auth_service
        )

        mock_auth_service.initiate_email_verification.assert_called_once_with(
            sample_user_id
        )


class TestConfirmEmailVerification:
    async def test_calls_verify_email(self, mock_auth_service):
        request = EmailVerificationConfirm(token="ev_token")

        await confirm_email_verification(request=request, auth_service=mock_auth_service)

        mock_auth_service.verify_email.assert_called_once_with("ev_token")

    async def test_raises_on_invalid_token(self, mock_auth_service):
        mock_auth_service.verify_email.side_effect = InvalidTokenError()
        request = EmailVerificationConfirm(token="invalid")

        with pytest.raises(InvalidTokenError):
            await confirm_email_verification(
                request=request, auth_service=mock_auth_service
            )
