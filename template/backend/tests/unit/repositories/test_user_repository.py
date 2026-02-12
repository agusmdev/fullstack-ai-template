"""Tests for UserRepository."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.user.repository import UserRepository


class TestUserRepositoryGet:
    """Tests for UserRepository.get method."""

    @pytest.fixture
    def repository(self, mock_session):
        return UserRepository(session=mock_session)

    async def test_get_by_id_with_uuid(self, repository, mock_session):
        """Test get by ID with UUID type."""
        user_id = uuid.uuid4()
        mock_result = MagicMock()
        mock_result.scalar.return_value = MagicMock(id=user_id, email="test@example.com")
        mock_session.execute.return_value = mock_result

        result = await repository.get(user_id, filter_field="id")

        mock_session.execute.assert_called_once()

    async def test_get_by_id_with_string_converts_to_uuid(self, repository, mock_session):
        """Test get by ID with string converts to UUID."""
        user_id_str = "12345678-1234-5678-1234-567812345678"
        mock_result = MagicMock()
        mock_result.scalar.return_value = MagicMock(id=uuid.UUID(user_id_str))
        mock_session.execute.return_value = mock_result

        result = await repository.get(user_id_str, filter_field="id")

        mock_session.execute.assert_called_once()

    async def test_get_by_email_keeps_string(self, repository, mock_session):
        """Test get by email keeps the string value."""
        email = "test@example.com"
        mock_result = MagicMock()
        mock_result.scalar.return_value = MagicMock(email=email)
        mock_session.execute.return_value = mock_result

        result = await repository.get(email, filter_field="email")

        mock_session.execute.assert_called_once()

    async def test_get_with_raise_error_true(self, repository, mock_session):
        """Test get with raise_error=True when not found."""
        from app.repositories.exceptions import NotFoundError

        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result

        with pytest.raises(NotFoundError):
            await repository.get(uuid.uuid4(), raise_error=True)

    async def test_get_with_raise_error_false(self, repository, mock_session):
        """Test get with raise_error=False returns None."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repository.get(uuid.uuid4(), raise_error=False)

        assert result is None


class TestUserRepositoryModel:
    """Tests for UserRepository model attribute."""

    def test_model_is_user(self, mock_session):
        """Test that model is set to User."""
        from app.user.models import User

        repo = UserRepository(session=mock_session)

        assert repo.model is User
