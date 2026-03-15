"""Tests for authentication repositories (Session, PasswordResetToken, EmailVerificationToken)."""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.user.auth.repository import (
    EmailVerificationTokenRepository,
    PasswordResetTokenRepository,
    SessionRepository,
)


@pytest.fixture
def mock_session():
    """Create a mock async session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


class TestSessionRepository:
    """Tests for SessionRepository."""

    @pytest.fixture
    def repo(self, mock_session):
        return SessionRepository(session=mock_session)

    async def test_get_by_string_id(self, repo, mock_session):
        """Test get with string session ID."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = MagicMock(id="session-abc")
        mock_session.execute.return_value = mock_result

        result = await repo.get("session-abc", raise_error=False)

        mock_session.execute.assert_called_once()

    async def test_delete_by_id(self, repo, mock_session):
        """Test deleting a session by string ID."""
        await repo.delete_by_id("session-abc")

        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_delete_all_for_user(self, repo, mock_session):
        """Test deleting all sessions for a user."""
        user_id = uuid.uuid4()
        await repo.delete_all_for_user(user_id)

        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()


class TestPasswordResetTokenRepository:
    """Tests for PasswordResetTokenRepository."""

    @pytest.fixture
    def repo(self, mock_session):
        return PasswordResetTokenRepository(session=mock_session)

    async def test_get_valid_token_found(self, repo, mock_session):
        """Test get_valid_token returns token when found."""
        mock_token = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_token
        mock_session.execute.return_value = mock_result

        result = await repo.get_valid_token("token-id-abc")

        assert result is mock_token
        mock_session.execute.assert_called_once()

    async def test_get_valid_token_not_found(self, repo, mock_session):
        """Test get_valid_token returns None when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_valid_token("invalid-token")

        assert result is None

    async def test_mark_as_used(self, repo, mock_session):
        """Test marking a token as used."""
        await repo.mark_as_used("token-id-abc")

        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_invalidate_user_tokens(self, repo, mock_session):
        """Test invalidating all tokens for a user."""
        user_id = uuid.uuid4()
        await repo.invalidate_user_tokens(user_id)

        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()


class TestEmailVerificationTokenRepository:
    """Tests for EmailVerificationTokenRepository."""

    @pytest.fixture
    def repo(self, mock_session):
        return EmailVerificationTokenRepository(session=mock_session)

    async def test_get_valid_token_found(self, repo, mock_session):
        """Test get_valid_token returns token when found."""
        mock_token = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_token
        mock_session.execute.return_value = mock_result

        result = await repo.get_valid_token("token-id-xyz")

        assert result is mock_token

    async def test_get_valid_token_not_found(self, repo, mock_session):
        """Test get_valid_token returns None when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_valid_token("expired-token")

        assert result is None

    async def test_mark_as_used(self, repo, mock_session):
        """Test marking an email verification token as used."""
        await repo.mark_as_used("token-id-xyz")

        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_invalidate_user_tokens(self, repo, mock_session):
        """Test invalidating all email verification tokens for a user."""
        user_id = uuid.uuid4()
        await repo.invalidate_user_tokens(user_id)

        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()
