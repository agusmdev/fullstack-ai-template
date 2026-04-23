"""Tests for User router endpoint functions."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.user.routers import delete_user, get_authenticated_user, update_logged_user
from app.user.schemas import UserUpdate


@pytest.fixture
def mock_user_service():
    svc = MagicMock()
    svc.update = AsyncMock()
    svc.delete = AsyncMock()
    return svc


@pytest.fixture
def sample_user_id():
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def mock_user(sample_user_id):
    user = MagicMock()
    user.id = sample_user_id
    user.email = "test@example.com"
    user.display_name = "Test User"
    user.email_verified_at = None
    return user


class TestGetAuthenticatedUser:
    async def test_returns_user_response(self, mock_user):
        result = await get_authenticated_user(user=mock_user)

        assert result.id == mock_user.id
        assert result.email == mock_user.email
        assert result.display_name == mock_user.display_name

    async def test_is_email_verified_false_when_no_verified_at(self, mock_user):
        mock_user.email_verified_at = None
        result = await get_authenticated_user(user=mock_user)
        assert result.is_email_verified is False


class TestUpdateLoggedUser:
    async def test_calls_service_update(self, mock_user_service, sample_user_id):
        user_update = UserUpdate(display_name="New Name")

        await update_logged_user(
            user_id=sample_user_id,
            user=user_update,
            user_service=mock_user_service,
        )

        mock_user_service.update.assert_called_once_with(sample_user_id, user_update)

    async def test_returns_none(self, mock_user_service, sample_user_id):
        user_update = UserUpdate(display_name="New Name")

        result = await update_logged_user(
            user_id=sample_user_id,
            user=user_update,
            user_service=mock_user_service,
        )

        assert result is None


class TestDeleteUser:
    async def test_calls_service_delete(self, mock_user_service, sample_user_id):
        await delete_user(
            user_id=sample_user_id,
            user_service=mock_user_service,
        )

        mock_user_service.delete.assert_called_once_with(sample_user_id)

    async def test_returns_none(self, mock_user_service, sample_user_id):
        result = await delete_user(
            user_id=sample_user_id,
            user_service=mock_user_service,
        )

        assert result is None
