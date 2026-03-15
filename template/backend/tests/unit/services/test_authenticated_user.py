"""Tests for AuthenticatedUser dependency class."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.user.auth.exceptions import SessionExpiredError
from app.user.auth.permissions import AuthenticatedUser
from app.user.auth.service import AuthService
from app.user.schemas import UserResponse


@pytest.fixture
def mock_auth_service():
    return MagicMock(spec=AuthService)


@pytest.fixture
def mock_http_auth():
    creds = MagicMock(spec=HTTPAuthorizationCredentials)
    creds.credentials = "s_test_session_token"
    return creds


@pytest.fixture
def sample_user_response():
    return UserResponse(
        id=uuid.uuid4(),
        email="test@example.com",
        display_name="Test User",
    )


@pytest.fixture
def mock_request():
    request = MagicMock()
    request.state = MagicMock()
    request.state.user = None
    del request.state.user  # simulate missing attribute
    return request


class TestAuthenticatedUserHttpAuth:
    """Tests for AuthenticatedUser.http_auth."""

    async def test_returns_credentials(self, mock_http_auth):
        result = await AuthenticatedUser.http_auth(mock_http_auth)
        assert result is mock_http_auth


class TestAuthenticatedUserGetUser:
    """Tests for AuthenticatedUser.get_user."""

    async def test_get_user_success(
        self, mock_request, mock_http_auth, mock_auth_service, sample_user_response
    ):
        """Test successful user retrieval."""
        mock_auth_service.check_session = AsyncMock(return_value=sample_user_response)

        with patch("app.user.auth.permissions.get_request_context") as mock_ctx, \
             patch("app.user.auth.permissions.log_user"):
            mock_ctx.return_value = MagicMock()
            result = await AuthenticatedUser.get_user(
                mock_request, mock_http_auth, mock_auth_service
            )

        assert result is sample_user_response
        mock_auth_service.check_session.assert_called_once_with("s_test_session_token")

    async def test_get_user_raises_401_on_exception(
        self, mock_request, mock_http_auth, mock_auth_service
    ):
        """Test that any exception raises 401 HTTPException."""
        mock_auth_service.check_session = AsyncMock(side_effect=SessionExpiredError())

        with pytest.raises(HTTPException) as exc_info:
            await AuthenticatedUser.get_user(
                mock_request, mock_http_auth, mock_auth_service
            )

        assert exc_info.value.status_code == 401

    async def test_get_user_returns_cached_user(
        self, mock_request, mock_http_auth, mock_auth_service, sample_user_response
    ):
        """Test that user is returned from request.state if already set."""
        mock_request.state.user = sample_user_response

        result = await AuthenticatedUser.get_user(
            mock_request, mock_http_auth, mock_auth_service
        )

        mock_auth_service.check_session.assert_not_called()
        assert result is sample_user_response


class TestAuthenticatedUserCurrentUserId:
    """Tests for AuthenticatedUser.current_user_id."""

    async def test_returns_user_id(
        self, mock_request, mock_http_auth, mock_auth_service, sample_user_response
    ):
        """Test returns user UUID."""
        mock_auth_service.check_session = AsyncMock(return_value=sample_user_response)

        with patch("app.user.auth.permissions.get_request_context") as mock_ctx, \
             patch("app.user.auth.permissions.log_user"):
            mock_ctx.return_value = MagicMock()
            result = await AuthenticatedUser.current_user_id(
                mock_request, mock_http_auth, mock_auth_service
            )

        assert result == sample_user_response.id
        assert isinstance(result, uuid.UUID)


class TestAuthenticatedUserCurrentUserEmail:
    """Tests for AuthenticatedUser.current_user_email."""

    async def test_returns_user_email(
        self, mock_request, mock_http_auth, mock_auth_service, sample_user_response
    ):
        """Test returns user email."""
        mock_auth_service.check_session = AsyncMock(return_value=sample_user_response)

        with patch("app.user.auth.permissions.get_request_context") as mock_ctx, \
             patch("app.user.auth.permissions.log_user"):
            mock_ctx.return_value = MagicMock()
            result = await AuthenticatedUser.current_user_email(
                mock_request, mock_http_auth, mock_auth_service
            )

        assert result == "test@example.com"
