"""Tests for user schemas."""

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.user.schemas import (
    UserBase,
    UserCreate,
    UserRegister,
    UserResponse,
    UserUpdate,
)


class TestUserBase:
    """Tests for UserBase schema."""

    def test_valid_user(self):
        """Test creating a valid user."""
        user = UserBase(email="test@example.com", display_name="Test User")
        assert user.email == "test@example.com"
        assert user.display_name == "Test User"

    def test_email_required(self):
        """Test that email is required."""
        with pytest.raises(ValidationError) as exc_info:
            UserBase(display_name="Test")
        assert "email" in str(exc_info.value)

    def test_invalid_email_format(self):
        """Test email validation."""
        with pytest.raises(ValidationError) as exc_info:
            UserBase(email="not-an-email", display_name="Test")
        assert "email" in str(exc_info.value)

    def test_display_name_default(self):
        """Test that display_name defaults to empty string."""
        user = UserBase(email="test@example.com")
        assert user.display_name == ""

    def test_various_valid_emails(self):
        """Test various valid email formats."""
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.com",
            "user@subdomain.example.com",
        ]
        for email in valid_emails:
            user = UserBase(email=email)
            assert user.email == email


class TestUserCreate:
    """Tests for UserCreate schema."""

    def test_inherits_from_user_base(self):
        """Test that UserCreate inherits from UserBase."""
        assert issubclass(UserCreate, UserBase)

    def test_create_user(self):
        """Test creating a user for creation."""
        user = UserCreate(email="new@example.com", display_name="New User")
        assert user.email == "new@example.com"
        assert user.display_name == "New User"


class TestUserRegister:
    """Tests for UserRegister schema with password hashing."""

    def test_valid_registration(self):
        """Test valid user registration."""
        user = UserRegister(
            email="register@example.com", display_name="New User", raw_password="secret123"
        )
        assert user.email == "register@example.com"
        assert user.display_name == "New User"
        assert user.raw_password == "secret123"

    def test_password_is_hashed(self):
        """Test that password computed field returns hashed value."""
        user = UserRegister(
            email="test@example.com", display_name="Test", raw_password="mypassword"
        )
        # Password should be hashed (Argon2 hash starts with $argon2)
        assert user.password.startswith("$argon2")
        assert user.password != "mypassword"

    def test_raw_password_excluded_from_dump(self):
        """Test that raw_password is excluded from model dump."""
        user = UserRegister(
            email="test@example.com", display_name="Test", raw_password="secret"
        )
        data = user.model_dump()
        assert "raw_password" not in data
        # But password (hashed) should be included
        assert "password" in data

    def test_different_passwords_produce_different_hashes(self):
        """Test that different passwords produce different hashes."""
        user1 = UserRegister(email="a@example.com", raw_password="password1")
        user2 = UserRegister(email="b@example.com", raw_password="password2")
        assert user1.password != user2.password

    def test_same_password_produces_different_hashes(self):
        """Test that same password produces different hashes (salting)."""
        user1 = UserRegister(email="a@example.com", raw_password="samepassword")
        user2 = UserRegister(email="b@example.com", raw_password="samepassword")
        # Argon2 uses random salt, so hashes should differ
        assert user1.password != user2.password


class TestUserUpdate:
    """Tests for UserUpdate schema (partial model)."""

    def test_all_fields_optional(self):
        """Test that all fields are optional for updates."""
        user = UserUpdate()
        assert user.email is None
        assert user.display_name is None

    def test_partial_update_email(self):
        """Test partial update with only email."""
        user = UserUpdate(email="newemail@example.com")
        assert user.email == "newemail@example.com"
        assert user.display_name is None

    def test_partial_update_display_name(self):
        """Test partial update with only display_name."""
        user = UserUpdate(display_name="New Name")
        assert user.email is None
        assert user.display_name == "New Name"

    def test_full_update(self):
        """Test update with all fields."""
        user = UserUpdate(email="updated@example.com", display_name="Updated User")
        assert user.email == "updated@example.com"
        assert user.display_name == "Updated User"


class TestUserResponse:
    """Tests for UserResponse schema."""

    def test_includes_id(self):
        """Test that response includes id field."""
        user = UserResponse(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            email="test@example.com",
            display_name="Test",
        )
        assert user.id == uuid.UUID("12345678-1234-5678-1234-567812345678")

    def test_from_attributes_mode(self):
        """Test that model has from_attributes config for ORM mode."""
        assert UserResponse.model_config.get("from_attributes") is True

    def test_email_verified_at_optional(self):
        """Test that email_verified_at is optional."""
        user = UserResponse(
            id=uuid.uuid4(),
            email="test@example.com",
        )
        assert user.email_verified_at is None

    def test_is_email_verified_computed_false(self):
        """Test is_email_verified computed field when not verified."""
        user = UserResponse(
            id=uuid.uuid4(),
            email="test@example.com",
            email_verified_at=None,
        )
        assert user.is_email_verified is False

    def test_is_email_verified_computed_true(self):
        """Test is_email_verified computed field when verified."""
        user = UserResponse(
            id=uuid.uuid4(),
            email="test@example.com",
            email_verified_at=datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC),
        )
        assert user.is_email_verified is True

    def test_json_serialization(self):
        """Test JSON serialization of response."""
        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        user = UserResponse(id=user_id, email="test@example.com", display_name="Test")
        json_data = user.model_dump_json()
        assert "12345678-1234-5678-1234-567812345678" in json_data
        assert "test@example.com" in json_data
        assert "is_email_verified" in json_data
