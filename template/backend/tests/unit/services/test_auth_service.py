"""Tests for AuthService."""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.user.auth.exceptions import (
    EmailAlreadyVerifiedError,
    InvalidTokenError,
    OAuthUserPasswordResetError,
    SessionExpiredError,
    UserNotFoundError,
)
from app.user.auth.schemas import SessionResponse
from app.user.auth.service import AuthService
from app.user.schemas import UserRegister, UserResponse
from app.user.service import UserService


class TestAuthServiceSessionId:
    """Tests for AuthService static methods."""

    def test_session_id_format(self):
        """Test session_id format."""
        session_id = AuthService.session_id()
        assert session_id.startswith("s_")
        assert len(session_id) > 10

    def test_session_id_unique(self):
        """Test session_id generates unique values."""
        ids = [AuthService.session_id() for _ in range(100)]
        assert len(set(ids)) == 100

    def test_generate_token_format(self):
        """Test generate_token format."""
        token = AuthService.generate_token("pr")
        assert token.startswith("pr_")

    def test_generate_token_unique(self):
        """Test generate_token generates unique values."""
        tokens = [AuthService.generate_token("t") for _ in range(100)]
        assert len(set(tokens)) == 100


class TestAuthServiceAuthenticate:
    """Tests for AuthService.authenticate method."""

    @pytest.fixture
    def mock_user_service(self, sample_user_model):
        service = MagicMock(spec=UserService)
        service.authenticate = AsyncMock(return_value=sample_user_model)
        return service

    @pytest.fixture
    def auth_service(self, mock_user_service, mock_session_repository):
        return AuthService(
            user_service=mock_user_service,
            repo=mock_session_repository,
        )

    async def test_authenticate_success(
        self, auth_service, mock_session_repository, sample_user_model
    ):
        """Test successful authentication creates session."""
        mock_session = MagicMock()
        mock_session.id = "s_test_session"
        mock_session.expires_at = datetime.now(tz=UTC) + timedelta(days=365)
        mock_session_repository.create.return_value = mock_session

        result = await auth_service.authenticate("test@example.com", "password")

        assert isinstance(result, SessionResponse)
        assert result.id == "s_test_session"
        mock_session_repository.create.assert_called_once()

    async def test_authenticate_creates_session_with_user_id(
        self, auth_service, mock_session_repository, mock_user_service, sample_user_model
    ):
        """Test authenticate creates session with correct user_id."""
        mock_session = MagicMock()
        mock_session.id = "s_test"
        mock_session.expires_at = datetime.now(tz=UTC)
        mock_session_repository.create.return_value = mock_session

        await auth_service.authenticate("test@example.com", "password")

        create_call = mock_session_repository.create.call_args[0][0]
        assert create_call.user_id == sample_user_model.id


class TestAuthServiceRegister:
    """Tests for AuthService.register method."""

    @pytest.fixture
    def mock_user_service(self, sample_user_model):
        service = MagicMock(spec=UserService)
        service.register = AsyncMock(
            return_value=UserResponse(
                id=sample_user_model.id,
                email=sample_user_model.email,
                display_name=sample_user_model.display_name,
            )
        )
        service.authenticate = AsyncMock(return_value=sample_user_model)
        return service

    @pytest.fixture
    def auth_service(self, mock_user_service, mock_session_repository):
        return AuthService(user_service=mock_user_service, repo=mock_session_repository)

    async def test_register_success(
        self, auth_service, mock_user_service, mock_session_repository
    ):
        """Test successful registration creates session."""
        mock_session = MagicMock()
        mock_session.id = "s_new_session"
        mock_session.expires_at = datetime.now(tz=UTC) + timedelta(days=365)
        mock_session_repository.create.return_value = mock_session

        user_data = UserRegister(
            email="new@example.com", display_name="New User", raw_password="password123"
        )
        result = await auth_service.register(user_data)

        mock_user_service.register.assert_called_once_with(user=user_data)
        assert isinstance(result, SessionResponse)


class TestAuthServiceCheckSession:
    """Tests for AuthService.check_session method."""

    @pytest.fixture
    def auth_service(self, mock_session_repository):
        mock_user_service = MagicMock(spec=UserService)
        return AuthService(user_service=mock_user_service, repo=mock_session_repository)

    async def test_check_session_valid(self, auth_service, mock_session_repository):
        """Test checking valid session."""
        mock_session = MagicMock()
        mock_session.expires_at = datetime.now() + timedelta(days=1)
        mock_session.user = UserResponse(
            id=uuid.uuid4(), email="test@example.com", display_name="Test"
        )
        mock_session_repository.get.return_value = mock_session

        result = await auth_service.check_session("s_valid_session")

        assert result == mock_session.user

    async def test_check_session_expired(self, auth_service, mock_session_repository):
        """Test checking expired session."""
        mock_session = MagicMock()
        mock_session.expires_at = datetime.now() - timedelta(days=1)
        mock_session.user = MagicMock()
        mock_session_repository.get.return_value = mock_session

        with pytest.raises(SessionExpiredError):
            await auth_service.check_session("s_expired_session")


class TestAuthServiceLogout:
    """Tests for AuthService.logout method."""

    @pytest.fixture
    def auth_service(self, mock_session_repository):
        mock_user_service = MagicMock(spec=UserService)
        return AuthService(user_service=mock_user_service, repo=mock_session_repository)

    async def test_logout_success(self, auth_service, mock_session_repository):
        """Test successful logout."""
        await auth_service.logout("s_session_to_delete")

        mock_session_repository.delete_by_id.assert_called_once_with("s_session_to_delete")

    async def test_logout_all_success(self, auth_service, mock_session_repository):
        """Test logout all sessions for user."""
        user_id = str(uuid.uuid4())

        await auth_service.logout_all(user_id)

        mock_session_repository.delete_all_for_user.assert_called_once()


class TestAuthServicePasswordReset:
    """Tests for AuthService password reset methods."""

    @pytest.fixture
    def mock_user_service(self, sample_user_model):
        service = MagicMock(spec=UserService)
        service.get = AsyncMock(return_value=sample_user_model)
        service.update_password = AsyncMock()
        return service

    @pytest.fixture
    def auth_service(
        self,
        mock_user_service,
        mock_session_repository,
        mock_password_reset_repository,
    ):
        return AuthService(
            user_service=mock_user_service,
            repo=mock_session_repository,
            password_reset_repo=mock_password_reset_repository,
        )

    async def test_initiate_password_reset_success(
        self, auth_service, mock_password_reset_repository, sample_user_model
    ):
        """Test initiating password reset for user with password."""
        sample_user_model.password = "hashed_password"

        result = await auth_service.initiate_password_reset("test@example.com")

        assert result is not None
        assert result.startswith("pr_")
        mock_password_reset_repository.invalidate_user_tokens.assert_called_once()
        mock_password_reset_repository.create.assert_called_once()

    async def test_initiate_password_reset_user_not_found(
        self, auth_service, mock_user_service
    ):
        """Test password reset for non-existent user returns None."""
        mock_user_service.get.return_value = None

        result = await auth_service.initiate_password_reset("nonexistent@example.com")

        assert result is None

    async def test_initiate_password_reset_oauth_user(
        self, auth_service, mock_user_service, sample_user_model
    ):
        """Test password reset for OAuth user raises error."""
        sample_user_model.password = None
        mock_user_service.get.return_value = sample_user_model

        with pytest.raises(OAuthUserPasswordResetError):
            await auth_service.initiate_password_reset("oauth@example.com")

    async def test_reset_password_success(
        self,
        auth_service,
        mock_password_reset_repository,
        mock_user_service,
        mock_session_repository,
    ):
        """Test successful password reset."""
        mock_token = MagicMock()
        mock_token.user_id = uuid.uuid4()
        mock_password_reset_repository.get_valid_token.return_value = mock_token

        await auth_service.reset_password("pr_valid_token", "new_password")

        mock_user_service.update_password.assert_called_once_with(
            mock_token.user_id, "new_password"
        )
        mock_password_reset_repository.mark_as_used.assert_called_once()
        mock_session_repository.delete_all_for_user.assert_called_once()

    async def test_reset_password_invalid_token(
        self, auth_service, mock_password_reset_repository
    ):
        """Test password reset with invalid token."""
        mock_password_reset_repository.get_valid_token.return_value = None

        with pytest.raises(InvalidTokenError):
            await auth_service.reset_password("pr_invalid", "new_password")


class TestAuthServiceEmailVerification:
    """Tests for AuthService email verification methods."""

    @pytest.fixture
    def mock_user_service(self, sample_user_model):
        service = MagicMock(spec=UserService)
        service.get = AsyncMock(return_value=sample_user_model)
        service.mark_email_verified = AsyncMock()
        return service

    @pytest.fixture
    def auth_service(
        self,
        mock_user_service,
        mock_session_repository,
        mock_email_verification_repository,
    ):
        return AuthService(
            user_service=mock_user_service,
            repo=mock_session_repository,
            email_verification_repo=mock_email_verification_repository,
        )

    async def test_initiate_email_verification_success(
        self, auth_service, mock_email_verification_repository, sample_user_model
    ):
        """Test initiating email verification."""
        sample_user_model.email_verified_at = None

        result = await auth_service.initiate_email_verification(sample_user_model.id)

        assert result.startswith("ev_")
        mock_email_verification_repository.create.assert_called_once()

    async def test_initiate_email_verification_user_not_found(
        self, auth_service, mock_user_service
    ):
        """Test email verification for non-existent user."""
        mock_user_service.get.return_value = None

        with pytest.raises(UserNotFoundError):
            await auth_service.initiate_email_verification(uuid.uuid4())

    async def test_initiate_email_verification_already_verified(
        self, auth_service, mock_user_service, sample_user_model
    ):
        """Test email verification when already verified."""
        sample_user_model.email_verified_at = datetime.now(tz=UTC)
        mock_user_service.get.return_value = sample_user_model

        with pytest.raises(EmailAlreadyVerifiedError):
            await auth_service.initiate_email_verification(sample_user_model.id)

    async def test_verify_email_success(
        self, auth_service, mock_email_verification_repository, mock_user_service
    ):
        """Test successful email verification."""
        mock_token = MagicMock()
        mock_token.user_id = uuid.uuid4()
        mock_email_verification_repository.get_valid_token.return_value = mock_token

        await auth_service.verify_email("ev_valid_token")

        mock_user_service.mark_email_verified.assert_called_once_with(mock_token.user_id)
        mock_email_verification_repository.mark_as_used.assert_called_once()

    async def test_verify_email_invalid_token(
        self, auth_service, mock_email_verification_repository
    ):
        """Test email verification with invalid token."""
        mock_email_verification_repository.get_valid_token.return_value = None

        with pytest.raises(InvalidTokenError):
            await auth_service.verify_email("ev_invalid")
