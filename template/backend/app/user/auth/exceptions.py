from app.exceptions import HTTPExceptionMixin


class AuthenticationError(HTTPExceptionMixin):
    """Base authentication error"""

    detail = "Authentication error"
    error_code = "authentication_error"
    status_code = 401


class InvalidPasswordError(AuthenticationError):
    """Invalid password error"""

    detail = "Invalid password"
    error_code = "invalid_password"
    status_code = 401


class SessionExpiredError(AuthenticationError):
    """Session expired error"""

    detail = "Session expired"
    error_code = "session_expired"
    status_code = 401


class InvalidTokenError(HTTPExceptionMixin):
    """Invalid or expired token error"""

    detail = "Invalid or expired token"
    error_code = "invalid_token"
    status_code = 400


class EmailAlreadyVerifiedError(HTTPExceptionMixin):
    """Email is already verified"""

    detail = "Email is already verified"
    error_code = "email_already_verified"
    status_code = 400


class UserNotFoundError(HTTPExceptionMixin):
    """User not found"""

    detail = "User not found"
    error_code = "user_not_found"
    status_code = 404


class OAuthUserPasswordResetError(HTTPExceptionMixin):
    """OAuth users cannot reset password"""

    detail = "Cannot reset password for OAuth users. Please sign in with your OAuth provider."
    error_code = "oauth_user_password_reset"
    status_code = 400
