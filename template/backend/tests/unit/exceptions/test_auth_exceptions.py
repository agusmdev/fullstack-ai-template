"""Tests for authentication exceptions."""

import pytest

from app.exceptions import HTTPExceptionMixin
from app.user.auth.exceptions import (
    AuthenticationError,
    EmailAlreadyVerifiedError,
    InvalidPasswordError,
    InvalidTokenError,
    OAuthUserPasswordResetError,
    SessionExpiredError,
    UserNotFoundError,
)


class TestAuthenticationError:
    """Tests for AuthenticationError exception."""

    def test_default_values(self):
        """Test default values for AuthenticationError."""
        exc = AuthenticationError()
        assert exc.status_code == 401
        assert exc.detail == "Authentication error"
        assert AuthenticationError.error_code == "authentication_error"

    def test_custom_detail(self):
        """Test custom detail message."""
        exc = AuthenticationError(detail="Invalid credentials provided")
        assert exc.detail == "Invalid credentials provided"
        assert exc.status_code == 401


class TestInvalidPasswordError:
    """Tests for InvalidPasswordError exception."""

    def test_default_values(self):
        """Test default values for InvalidPasswordError."""
        exc = InvalidPasswordError()
        assert exc.status_code == 401
        assert exc.detail == "Invalid password"
        assert InvalidPasswordError.error_code == "invalid_password"

    def test_inherits_from_authentication_error(self):
        """Test that InvalidPasswordError inherits from AuthenticationError."""
        exc = InvalidPasswordError()
        assert isinstance(exc, AuthenticationError)


class TestSessionExpiredError:
    """Tests for SessionExpiredError exception."""

    def test_default_values(self):
        """Test default values for SessionExpiredError."""
        exc = SessionExpiredError()
        assert exc.status_code == 401
        assert exc.detail == "Session expired"
        assert SessionExpiredError.error_code == "session_expired"

    def test_inherits_from_authentication_error(self):
        """Test that SessionExpiredError inherits from AuthenticationError."""
        exc = SessionExpiredError()
        assert isinstance(exc, AuthenticationError)


class TestInvalidTokenError:
    """Tests for InvalidTokenError exception."""

    def test_default_values(self):
        """Test default values for InvalidTokenError."""
        exc = InvalidTokenError()
        assert exc.status_code == 400
        assert exc.detail == "Invalid or expired token"
        assert InvalidTokenError.error_code == "invalid_token"

    def test_inherits_from_http_exception_mixin(self):
        """Test that InvalidTokenError inherits from HTTPExceptionMixin."""
        exc = InvalidTokenError()
        assert isinstance(exc, HTTPExceptionMixin)


class TestEmailAlreadyVerifiedError:
    """Tests for EmailAlreadyVerifiedError exception."""

    def test_default_values(self):
        """Test default values for EmailAlreadyVerifiedError."""
        exc = EmailAlreadyVerifiedError()
        assert exc.status_code == 400
        assert exc.detail == "Email is already verified"
        assert EmailAlreadyVerifiedError.error_code == "email_already_verified"


class TestUserNotFoundError:
    """Tests for UserNotFoundError exception."""

    def test_default_values(self):
        """Test default values for UserNotFoundError."""
        exc = UserNotFoundError()
        assert exc.status_code == 404
        assert exc.detail == "User not found"
        assert UserNotFoundError.error_code == "user_not_found"


class TestOAuthUserPasswordResetError:
    """Tests for OAuthUserPasswordResetError exception."""

    def test_default_values(self):
        """Test default values for OAuthUserPasswordResetError."""
        exc = OAuthUserPasswordResetError()
        assert exc.status_code == 400
        assert (
            exc.detail
            == "Cannot reset password for OAuth users. Please sign in with your OAuth provider."
        )
        assert OAuthUserPasswordResetError.error_code == "oauth_user_password_reset"


class TestAuthExceptionHierarchy:
    """Tests for auth exception inheritance hierarchy."""

    def test_all_inherit_from_http_exception_mixin(self):
        """Test all auth exceptions inherit from HTTPExceptionMixin."""
        exceptions = [
            AuthenticationError,
            InvalidPasswordError,
            SessionExpiredError,
            InvalidTokenError,
            EmailAlreadyVerifiedError,
            UserNotFoundError,
            OAuthUserPasswordResetError,
        ]
        for exc_class in exceptions:
            exc = exc_class()
            assert isinstance(exc, HTTPExceptionMixin)

    def test_catch_all_authentication_errors(self):
        """Test that auth errors can be caught with AuthenticationError."""
        auth_errors = [InvalidPasswordError, SessionExpiredError]
        for exc_class in auth_errors:
            with pytest.raises(AuthenticationError):
                raise exc_class()
