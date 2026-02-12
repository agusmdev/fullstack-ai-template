"""Tests for authentication schemas."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.user.auth.schemas import (
    EmailVerificationConfirm,
    EmailVerificationConfirmResponse,
    EmailVerificationRequest,
    EmailVerificationResponse,
    EmailVerificationTokenCreate,
    LogoutResponse,
    OAuthCallback,
    OAuthUser,
    PasswordResetConfirm,
    PasswordResetConfirmResponse,
    PasswordResetRequest,
    PasswordResetResponse,
    PasswordResetTokenCreate,
    SessionBase,
    SessionCreate,
    SessionResponse,
    UserSessionResponse,
)
from app.user.schemas import UserResponse


class TestSessionBase:
    """Tests for SessionBase schema."""

    def test_valid_session(self):
        """Test creating a valid session."""
        expires = datetime.now(tz=UTC) + timedelta(days=1)
        session = SessionBase(id="session_abc123", expires_at=expires)
        assert session.id == "session_abc123"
        assert session.expires_at == expires

    def test_session_id_required(self):
        """Test that session id is required."""
        with pytest.raises(ValidationError):
            SessionBase(expires_at=datetime.now(tz=UTC))

    def test_expires_at_required(self):
        """Test that expires_at is required."""
        with pytest.raises(ValidationError):
            SessionBase(id="session_123")


class TestSessionResponse:
    """Tests for SessionResponse schema."""

    def test_expires_in_computed(self):
        """Test expires_in computed field."""
        future_time = datetime.now() + timedelta(hours=1)
        session = SessionResponse(id="session_123", expires_at=future_time)
        # Should be approximately 3600 seconds (1 hour)
        assert 3500 < session.expires_in < 3700

    def test_expires_in_negative_for_expired(self):
        """Test expires_in is negative for expired sessions."""
        past_time = datetime.now() - timedelta(hours=1)
        session = SessionResponse(id="session_123", expires_at=past_time)
        assert session.expires_in < 0


class TestSessionCreate:
    """Tests for SessionCreate schema."""

    def test_includes_user_id(self):
        """Test that SessionCreate includes user_id."""
        user_id = uuid.uuid4()
        session = SessionCreate(
            id="session_123",
            expires_at=datetime.now(tz=UTC) + timedelta(days=1),
            user_id=user_id,
        )
        assert session.user_id == user_id

    def test_user_id_required(self):
        """Test that user_id is required."""
        with pytest.raises(ValidationError):
            SessionCreate(id="session_123", expires_at=datetime.now(tz=UTC))


class TestUserSessionResponse:
    """Tests for UserSessionResponse schema."""

    def test_includes_user(self):
        """Test that response includes user object."""
        user = UserResponse(id=uuid.uuid4(), email="test@example.com", display_name="Test")
        session = UserSessionResponse(
            id="session_123",
            expires_at=datetime.now(tz=UTC) + timedelta(days=1),
            user=user,
        )
        assert session.user.email == "test@example.com"


class TestOAuthCallback:
    """Tests for OAuthCallback schema."""

    def test_minimal_callback(self):
        """Test callback with only required fields."""
        callback = OAuthCallback(code="auth_code_123")
        assert callback.code == "auth_code_123"
        assert callback.state is None

    def test_full_callback(self):
        """Test callback with all fields."""
        callback = OAuthCallback(
            code="auth_code_123",
            state="state_xyz",
            redirect_url="https://example.com/callback",
            access_token="access_123",
            refresh_token="refresh_456",
            expires_in=3600,
        )
        assert callback.code == "auth_code_123"
        assert callback.state == "state_xyz"
        assert callback.access_token == "access_123"

    def test_error_callback(self):
        """Test callback with error fields."""
        callback = OAuthCallback(
            code="",
            error="access_denied",
            error_description="User denied access",
        )
        assert callback.error == "access_denied"
        assert callback.error_description == "User denied access"


class TestOAuthUser:
    """Tests for OAuthUser schema."""

    def test_valid_oauth_user(self):
        """Test creating valid OAuth user."""
        user = OAuthUser(
            token="oauth_token_123",
            email="oauth@example.com",
            display_name="OAuth User",
        )
        assert user.token == "oauth_token_123"
        assert user.email == "oauth@example.com"
        assert user.display_name == "OAuth User"

    def test_email_validation(self):
        """Test email validation on OAuth user."""
        with pytest.raises(ValidationError):
            OAuthUser(token="token", email="not-valid", display_name="Test")


class TestLogoutResponse:
    """Tests for LogoutResponse schema."""

    def test_default_values(self):
        """Test default logout response values."""
        response = LogoutResponse()
        assert response.status == "logged_out"
        assert response.message == "Successfully logged out"


class TestPasswordResetSchemas:
    """Tests for password reset related schemas."""

    def test_password_reset_token_create(self):
        """Test creating password reset token."""
        user_id = uuid.uuid4()
        token = PasswordResetTokenCreate(
            id="pr_token_123",
            expires_at=datetime.now(tz=UTC) + timedelta(hours=1),
            user_id=user_id,
        )
        assert token.id == "pr_token_123"
        assert token.user_id == user_id

    def test_password_reset_request(self):
        """Test password reset request."""
        request = PasswordResetRequest(email="user@example.com")
        assert request.email == "user@example.com"

    def test_password_reset_request_invalid_email(self):
        """Test password reset request with invalid email."""
        with pytest.raises(ValidationError):
            PasswordResetRequest(email="not-an-email")

    def test_password_reset_confirm(self):
        """Test password reset confirm."""
        confirm = PasswordResetConfirm(token="reset_token_123", new_password="newpassword123")
        assert confirm.token == "reset_token_123"
        assert confirm.new_password == "newpassword123"

    def test_password_reset_response(self):
        """Test password reset response defaults."""
        response = PasswordResetResponse()
        assert response.status == "success"
        assert response.message == "Password reset email sent"

    def test_password_reset_confirm_response(self):
        """Test password reset confirm response."""
        response = PasswordResetConfirmResponse()
        assert response.status == "success"
        assert response.message == "Password has been reset successfully"


class TestEmailVerificationSchemas:
    """Tests for email verification related schemas."""

    def test_email_verification_token_create(self):
        """Test creating email verification token."""
        user_id = uuid.uuid4()
        token = EmailVerificationTokenCreate(
            id="ev_token_123",
            expires_at=datetime.now(tz=UTC) + timedelta(hours=24),
            user_id=user_id,
        )
        assert token.id == "ev_token_123"
        assert token.user_id == user_id

    def test_email_verification_request(self):
        """Test email verification request (empty body)."""
        request = EmailVerificationRequest()
        assert request is not None

    def test_email_verification_confirm(self):
        """Test email verification confirm."""
        confirm = EmailVerificationConfirm(token="verify_token_123")
        assert confirm.token == "verify_token_123"

    def test_email_verification_response(self):
        """Test email verification response defaults."""
        response = EmailVerificationResponse()
        assert response.status == "success"
        assert response.message == "Verification email sent"

    def test_email_verification_confirm_response(self):
        """Test email verification confirm response."""
        response = EmailVerificationConfirmResponse()
        assert response.status == "success"
        assert response.message == "Email has been verified successfully"
