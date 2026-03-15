"""Tests for UserService."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from argon2.exceptions import VerifyMismatchError

from app.user.auth.exceptions import AuthenticationError, InvalidPasswordError
from app.user.schemas import UserRegister, UserResponse
from app.user.service import UserService


class TestUserServiceGet:
    """Tests for UserService.get_by_id and get_by_field methods."""

    @pytest.fixture
    def service(self, mock_user_repository):
        return UserService(repo=mock_user_repository)

    async def test_get_by_id(self, service, mock_user_repository, sample_user_model):
        """Test get user by UUID id."""
        mock_user_repository.get.return_value = sample_user_model

        result = await service.get_by_id(sample_user_model.id)

        mock_user_repository.get.assert_called_once_with(
            sample_user_model.id, raise_error=True
        )
        assert result == sample_user_model

    async def test_get_by_email(self, service, mock_user_repository, sample_user_model):
        """Test get user by email via get_by_field."""
        mock_user_repository.get_by_field.return_value = sample_user_model

        result = await service.get_by_field("email", "test@example.com")

        mock_user_repository.get_by_field.assert_called_once_with(
            "email", "test@example.com", raise_error=True, response_model=None
        )
        assert result == sample_user_model

    async def test_get_not_found_raise_false(self, service, mock_user_repository):
        """Test get user not found with raise_error=False."""
        mock_user_repository.get.return_value = None

        result = await service.get_by_id(uuid.uuid4(), raise_error=False)

        assert result is None


class TestUserServiceGetOrCreate:
    """Tests for UserService.get_or_create method."""

    @pytest.fixture
    def service(self, mock_user_repository):
        return UserService(repo=mock_user_repository)

    async def test_get_or_create_existing_user(
        self, service, mock_user_repository, sample_user_model
    ):
        """Test get_or_create returns existing user."""
        mock_user_repository.get_by_field.return_value = sample_user_model
        create_fields = MagicMock()

        result = await service.find_or_create("email", sample_user_model.email, create_fields)

        mock_user_repository.get_by_field.assert_called_once()
        mock_user_repository.create.assert_not_called()
        assert result == sample_user_model

    async def test_get_or_create_new_user(self, service, mock_user_repository, sample_user_model):
        """Test get_or_create creates new user when not found."""
        mock_user_repository.get_by_field.return_value = None
        mock_user_repository.create.return_value = sample_user_model
        create_fields = MagicMock()

        result = await service.find_or_create("email", "new@example.com", create_fields)

        mock_user_repository.get_by_field.assert_called_once()
        mock_user_repository.create.assert_called_once_with(create_fields)
        assert result == sample_user_model


class TestUserServiceRegister:
    """Tests for UserService.register method."""

    @pytest.fixture
    def service(self, mock_user_repository):
        return UserService(repo=mock_user_repository)

    async def test_register_success(self, service, mock_user_repository, sample_user_model):
        """Test successful user registration."""
        mock_user_repository.create.return_value = sample_user_model
        register_data = UserRegister(
            email="new@example.com", display_name="New User", raw_password="password123"
        )

        result = await service.register(register_data)

        mock_user_repository.create.assert_called_once_with(register_data)
        assert isinstance(result, UserResponse)
        assert result.id == sample_user_model.id
        assert result.email == sample_user_model.email

    async def test_register_returns_user_response(
        self, service, mock_user_repository, sample_user_model
    ):
        """Test that register returns UserResponse type."""
        mock_user_repository.create.return_value = sample_user_model
        register_data = UserRegister(
            email="test@example.com", display_name="Test", raw_password="password"
        )

        result = await service.register(register_data)

        assert isinstance(result, UserResponse)
        assert result.display_name == sample_user_model.display_name


class TestUserServiceAuthenticate:
    """Tests for UserService.authenticate method."""

    @pytest.fixture
    def service(self, mock_user_repository):
        return UserService(repo=mock_user_repository)

    async def test_authenticate_success(self, service, mock_user_repository, sample_user_model):
        """Test successful authentication."""
        mock_user_repository.get_by_field.return_value = sample_user_model

        result = await service.authenticate("test@example.com", "correct_password")

        mock_user_repository.get_by_field.assert_called_once_with(
            "email", "test@example.com", raise_error=False
        )
        assert result == sample_user_model

    async def test_authenticate_user_not_found(self, service, mock_user_repository):
        """Test authentication with non-existent user."""
        mock_user_repository.get_by_field.return_value = None

        with pytest.raises(AuthenticationError) as exc_info:
            await service.authenticate("nonexistent@example.com", "password")

        assert "does not exist" in exc_info.value.detail

    async def test_authenticate_wrong_password(
        self, service, mock_user_repository, sample_user_model
    ):
        """Test authentication with wrong password."""
        mock_user_repository.get_by_field.return_value = sample_user_model

        with pytest.raises(InvalidPasswordError):
            await service.authenticate("test@example.com", "wrong_password")


class TestUserServiceUpdatePassword:
    """Tests for UserService.update_password method."""

    @pytest.fixture
    def service(self, mock_user_repository):
        return UserService(repo=mock_user_repository)

    async def test_update_password_success(self, service, mock_user_repository, sample_user_id):
        """Test successful password update."""
        mock_user_repository.update.return_value = MagicMock()

        await service.update_password(sample_user_id, "new_password123")

        mock_user_repository.update.assert_called_once()
        call_args = mock_user_repository.update.call_args
        assert call_args[0][0] == sample_user_id
        # Password should be hashed
        assert call_args[0][1]["password"].startswith("$argon2")

    async def test_update_password_hashes_password(
        self, service, mock_user_repository, sample_user_id
    ):
        """Test that password is properly hashed."""
        mock_user_repository.update.return_value = MagicMock()

        await service.update_password(sample_user_id, "plaintext_password")

        call_args = mock_user_repository.update.call_args
        stored_password = call_args[0][1]["password"]
        # Argon2 hashes start with $argon2
        assert stored_password != "plaintext_password"
        assert stored_password.startswith("$argon2")


class TestUserServiceMarkEmailVerified:
    """Tests for UserService.mark_email_verified method."""

    @pytest.fixture
    def service(self, mock_user_repository):
        return UserService(repo=mock_user_repository)

    async def test_mark_email_verified_success(
        self, service, mock_user_repository, sample_user_id
    ):
        """Test successful email verification marking."""
        mock_user_repository.update.return_value = MagicMock()

        await service.mark_email_verified(sample_user_id)

        mock_user_repository.update.assert_called_once()
        call_args = mock_user_repository.update.call_args
        assert call_args[0][0] == sample_user_id
        assert "email_verified_at" in call_args[0][1]
        assert isinstance(call_args[0][1]["email_verified_at"], datetime)
