"""Tests for User model."""

import uuid
from datetime import UTC, datetime

import pytest
from argon2 import PasswordHasher

from app.user.models import User


class TestUserModel:
    """Tests for User model class."""

    def test_user_creation(self):
        """Test creating a User instance."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            display_name="Test User",
            is_active=True,
        )
        assert user.email == "test@example.com"
        assert user.display_name == "Test User"
        assert user.is_active is True

    def test_user_tablename(self):
        """Test that tablename is correctly set."""
        assert User.__tablename__ == "user"


class TestCheckPassword:
    """Tests for User.check_password method."""

    @pytest.fixture
    def user_with_password(self):
        """Create a user with a hashed password."""
        ph = PasswordHasher()
        hashed = ph.hash("correct_password")
        return User(
            id=uuid.uuid4(),
            email="test@example.com",
            display_name="Test User",
            password=hashed,
        )

    @pytest.fixture
    def user_without_password(self):
        """Create a user without a password (OAuth user)."""
        return User(
            id=uuid.uuid4(),
            email="oauth@example.com",
            display_name="OAuth User",
            password=None,
        )

    def test_correct_password_returns_true(self, user_with_password):
        """Test that correct password returns True."""
        result = user_with_password.check_password("correct_password")
        assert result is True

    def test_incorrect_password_returns_false(self, user_with_password):
        """Test that incorrect password returns False."""
        result = user_with_password.check_password("wrong_password")
        assert result is False

    def test_none_password_returns_false(self, user_without_password):
        """Test that checking password when password is None returns False."""
        result = user_without_password.check_password("any_password")
        assert result is False

    def test_empty_password_returns_false(self, user_with_password):
        """Test that empty password returns False."""
        result = user_with_password.check_password("")
        assert result is False


class TestIsEmailVerified:
    """Tests for User.is_email_verified property."""

    def test_not_verified_when_none(self):
        """Test that is_email_verified is False when email_verified_at is None."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            email_verified_at=None,
        )
        assert user.is_email_verified is False

    def test_verified_when_set(self):
        """Test that is_email_verified is True when email_verified_at is set."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            email_verified_at=datetime.now(tz=UTC),
        )
        assert user.is_email_verified is True

    def test_verified_with_past_date(self):
        """Test that verification works with past dates."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            email_verified_at=datetime(2020, 1, 1, tzinfo=UTC),
        )
        assert user.is_email_verified is True


class TestUserDefaults:
    """Tests for User model default values."""

    def test_default_is_active(self):
        """Test that is_active defaults to True."""
        user = User(id=uuid.uuid4(), email="test@example.com")
        # Default should be True based on model definition
        assert User.is_active.default.arg is True

    def test_display_name_server_default(self):
        """Test that display_name has empty string server default."""
        # Check the column definition
        assert User.display_name.server_default.arg == ""
