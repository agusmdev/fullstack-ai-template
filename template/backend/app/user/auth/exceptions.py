from app.exceptions import HTTPExceptionMixin


class AuthenticationError(HTTPExceptionMixin):
    detail = "Authentication error"
    error_code = "authentication_error"
    status_code = 401


class InvalidPasswordError(AuthenticationError):
    detail = "Invalid password"
    error_code = "invalid_password"
    status_code = 401


class SessionExpiredError(AuthenticationError):
    detail = "Session expired"
    error_code = "session_expired"
    status_code = 401


class InvalidTokenError(HTTPExceptionMixin):
    detail = "Invalid or expired token"
    error_code = "invalid_token"
    status_code = 400


class EmailAlreadyVerifiedError(HTTPExceptionMixin):
    detail = "Email is already verified"
    error_code = "email_already_verified"
    status_code = 400


class UserNotFoundError(HTTPExceptionMixin):
    detail = "User not found"
    error_code = "user_not_found"
    status_code = 404


class OAuthUserPasswordResetError(HTTPExceptionMixin):
    detail = "Cannot reset password for OAuth users. Please sign in with your OAuth provider."
    error_code = "oauth_user_password_reset"
    status_code = 400


class UnsupportedOAuthProviderError(HTTPExceptionMixin):
    detail = "Unsupported OAuth provider"
    error_code = "unsupported_oauth_provider"
    status_code = 400
