import secrets
import uuid
from datetime import datetime, timedelta
from typing import cast

import loguru
from requests_oauthlib import OAuth2Session

from app.core.config import settings
from app.services.base_crud_service import BaseService
from app.user.auth.exceptions import (
    EmailAlreadyVerifiedError,
    InvalidTokenError,
    OAuthUserPasswordResetError,
    SessionExpiredError,
    UserNotFoundError,
)
from app.user.auth.models import Session
from app.user.auth.repository import (
    EmailVerificationTokenRepository,
    PasswordResetTokenRepository,
    SessionRepository,
)
from app.user.auth.schemas import (
    EmailVerificationTokenCreate,
    OAuthCallback,
    OAuthUser,
    PasswordResetTokenCreate,
    SessionCreate,
    SessionResponse,
    UserSessionResponse,
)
from app.user.schemas import UserCreate, UserRegister, UserResponse
from app.user.service import UserService

# Token expiration times
PASSWORD_RESET_TOKEN_EXPIRY_HOURS = 1
EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS = 24


class GoogleOAuth:
    def callback(self, callback: OAuthCallback) -> OAuthUser:
        google = OAuth2Session(
            client_id=settings.GOOGLE_CLIENT_ID,
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
            state=callback.state,
            scope="https://www.googleapis.com/auth/userinfo.profile openid https://www.googleapis.com/auth/userinfo.email",
        )

        token = google.fetch_token(
            "https://oauth2.googleapis.com/token",
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            code=callback.code,
        )

        user_info_response = google.get(settings.GOOGLE_USER_INFO_URL)
        user_info = user_info_response.json()

        user_email = user_info.get("email")
        user_name = user_info.get("name")

        return OAuthUser(
            token=token["access_token"],
            email=user_email,
            display_name=user_name,
        )


class AuthService(BaseService[Session]):
    repo: SessionRepository
    user_service: UserService
    password_reset_repo: PasswordResetTokenRepository | None
    email_verification_repo: EmailVerificationTokenRepository | None

    def __init__(
        self,
        user_service: UserService,
        repo: SessionRepository,
        password_reset_repo: PasswordResetTokenRepository | None = None,
        email_verification_repo: EmailVerificationTokenRepository | None = None,
    ) -> None:
        self.user_service = user_service
        self.repo = repo
        self.password_reset_repo = password_reset_repo
        self.email_verification_repo = email_verification_repo

        self.providers = {
            "google": GoogleOAuth(),
        }

    @staticmethod
    def session_id() -> str:
        return f"s_{secrets.token_urlsafe(64)}"

    @staticmethod
    def generate_token(prefix: str = "t") -> str:
        """Generate a secure random token with a prefix."""
        return f"{prefix}_{secrets.token_urlsafe(32)}"

    async def authenticate(self, email: str, password: str) -> SessionResponse:
        user = await self.user_service.authenticate(email=email, password=password)

        created_session = await self.repo.create(
            SessionCreate(
                id=self.session_id(),
                user_id=user.id,
                expires_at=datetime.now() + timedelta(days=365),
            )
        )

        return SessionResponse(
            id=created_session.id,
            expires_at=created_session.expires_at,
        )

    async def register(self, new_user: UserRegister) -> SessionResponse:
        await self.user_service.register(user=new_user)
        return await self.authenticate(
            email=new_user.email, password=new_user.raw_password
        )

    async def oauth_login(
        self, provider_name: str, payload: OAuthCallback
    ) -> SessionResponse:
        provider = self.providers.get(provider_name)
        if not provider:
            raise ValueError("Unsupported provider")

        oauth_user = provider.callback(payload)
        user = await self.user_service.get_or_create(
            oauth_user.email,
            filter_field="email",
            create_fields=UserCreate(
                email=oauth_user.email,
                display_name=oauth_user.display_name or "",
            ),
        )

        created_session = await self.repo.create(
            SessionCreate(
                id=self.session_id(),
                user_id=user.id,
                expires_at=datetime.now() + timedelta(days=365),
            )
        )

        return SessionResponse(
            id=created_session.id,
            expires_at=created_session.expires_at,
        )

    async def check_session(self, session_id: str) -> UserResponse:
        session = cast(
            "UserSessionResponse",
            await self.repo.get(
                session_id, response_model=UserSessionResponse, raise_error=True
            ),
        )
        if session is None:
            raise SessionExpiredError()
        if session.expires_at < datetime.now():
            raise SessionExpiredError()
        # Return the user from the session
        return session.user

    async def logout(self, session_id: str) -> None:
        """Invalidate a session by deleting it."""
        await self.repo.delete_by_id(session_id)

    async def logout_all(self, user_id: str) -> None:
        """Invalidate all sessions for a user (logout from all devices)."""
        await self.repo.delete_all_for_user(uuid.UUID(user_id))

    # Password Reset Methods

    async def initiate_password_reset(self, email: str) -> str | None:
        """
        Initiate password reset process.

        Returns the token if successful (for sending via email).
        Returns None if user not found (to prevent email enumeration).
        Raises OAuthUserPasswordResetError if user is OAuth-only.
        """
        if not self.password_reset_repo:
            raise RuntimeError("Password reset repository not configured")

        # Get user by email
        user = await self.user_service.get(
            email, filter_field="email", raise_error=False
        )
        if not user:
            # Return None silently to prevent email enumeration
            loguru.logger.info(
                f"Password reset requested for non-existent email: {email}"
            )
            return None

        # Check if user has a password (not OAuth-only)
        if user.password is None:
            raise OAuthUserPasswordResetError()

        # Invalidate any existing tokens for this user
        await self.password_reset_repo.invalidate_user_tokens(user.id)

        # Create new token
        token = self.generate_token("pr")
        await self.password_reset_repo.create(
            PasswordResetTokenCreate(
                id=token,
                user_id=user.id,
                expires_at=datetime.now()
                + timedelta(hours=PASSWORD_RESET_TOKEN_EXPIRY_HOURS),
            )
        )

        loguru.logger.info(f"Password reset token created for user: {user.id}")
        return token

    async def reset_password(self, token: str, new_password: str) -> None:
        """
        Reset password using a valid token.

        Raises InvalidTokenError if token is invalid or expired.
        """
        if not self.password_reset_repo:
            raise RuntimeError("Password reset repository not configured")

        # Validate token
        token_record = await self.password_reset_repo.get_valid_token(token)
        if not token_record:
            raise InvalidTokenError()

        # Update user password
        await self.user_service.update_password(token_record.user_id, new_password)

        # Mark token as used
        await self.password_reset_repo.mark_as_used(token)

        # Optionally: logout all sessions for security
        await self.repo.delete_all_for_user(token_record.user_id)

        loguru.logger.info(f"Password reset completed for user: {token_record.user_id}")

    # Email Verification Methods

    async def initiate_email_verification(self, user_id: uuid.UUID) -> str:
        """
        Initiate email verification process.

        Returns the token for sending via email.
        Raises UserNotFoundError if user not found.
        Raises EmailAlreadyVerifiedError if already verified.
        """
        if not self.email_verification_repo:
            raise RuntimeError("Email verification repository not configured")

        # Get user
        user = await self.user_service.get(user_id, raise_error=False)
        if not user:
            raise UserNotFoundError()

        # Check if already verified
        if user.email_verified_at is not None:
            raise EmailAlreadyVerifiedError()

        # Invalidate any existing tokens
        await self.email_verification_repo.invalidate_user_tokens(user_id)

        # Create new token
        token = self.generate_token("ev")
        await self.email_verification_repo.create(
            EmailVerificationTokenCreate(
                id=token,
                user_id=user_id,
                expires_at=datetime.now()
                + timedelta(hours=EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS),
            )
        )

        loguru.logger.info(f"Email verification token created for user: {user_id}")
        return token

    async def verify_email(self, token: str) -> None:
        """
        Verify email using a valid token.

        Raises InvalidTokenError if token is invalid or expired.
        """
        if not self.email_verification_repo:
            raise RuntimeError("Email verification repository not configured")

        # Validate token
        token_record = await self.email_verification_repo.get_valid_token(token)
        if not token_record:
            raise InvalidTokenError()

        # Mark email as verified
        await self.user_service.mark_email_verified(token_record.user_id)

        # Mark token as used
        await self.email_verification_repo.mark_as_used(token)

        loguru.logger.info(f"Email verified for user: {token_record.user_id}")
