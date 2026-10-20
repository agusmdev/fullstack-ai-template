import asyncio
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import requests
from oauthlib.oauth2 import OAuth2Error
from requests_oauthlib import OAuth2Session

from app.core.config import settings
from app.user.auth.exceptions import (
    EmailAlreadyVerifiedError,
    InactiveUserError,
    InvalidTokenError,
    OAuthProviderError,
    OAuthUserPasswordResetError,
    SessionExpiredError,
    UnsupportedOAuthProviderError,
    UserNotFoundError,
)
from app.user.auth.repository import (
    EmailVerificationTokenRepository,
    PasswordResetTokenRepository,
    SessionRepository,
)
from app.user.auth.schemas import (
    OAuthCallback,
    OAuthUser,
    SessionResponse,
    TokenCreate,
    UserSessionResponse,
)
from app.user.models import User
from app.user.schemas import UserCreate, UserRegister
from app.user.service import UserService

# Token expiration times
PASSWORD_RESET_TOKEN_EXPIRY_HOURS = 1
EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS = 24


class GoogleOAuth:
    async def callback(self, callback: OAuthCallback) -> OAuthUser:
        """Exchange OAuth callback code for user info. Network I/O runs in a thread pool."""
        return await asyncio.to_thread(self._fetch_user, callback)

    def _fetch_user(self, callback: OAuthCallback) -> OAuthUser:
        try:
            return self._exchange_code(callback)
        except (OAuth2Error, requests.RequestException, ValueError) as err:
            # Google rejected the code (expired, already used, wrong client
            # secret), was unreachable, or sent a user without an email
            # (ValueError covers bad JSON and pydantic's ValidationError).
            raise OAuthProviderError() from err

    def _exchange_code(self, callback: OAuthCallback) -> OAuthUser:
        google = OAuth2Session(
            client_id=settings.GOOGLE_CLIENT_ID,
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
            state=callback.state,
            scope="https://www.googleapis.com/auth/userinfo.profile openid https://www.googleapis.com/auth/userinfo.email",
        )

        token = google.fetch_token(
            settings.GOOGLE_TOKEN_URL,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            code=callback.code,
            timeout=10,
        )

        response = google.get(settings.GOOGLE_USER_INFO_URL, timeout=10)
        response.raise_for_status()
        user_info = response.json()

        return OAuthUser(
            token=token["access_token"],
            email=user_info.get("email"),
            email_verified=user_info.get("verified_email") is True,
            display_name=user_info.get("name"),
        )


OAUTH_PROVIDERS: dict[str, type[GoogleOAuth]] = {"google": GoogleOAuth}
OAUTH_PROVIDER_NAMES: frozenset[str] = frozenset(OAUTH_PROVIDERS)


class AuthService:
    repo: SessionRepository
    user_service: UserService
    password_reset_repo: PasswordResetTokenRepository
    email_verification_repo: EmailVerificationTokenRepository

    def __init__(
        self,
        user_service: UserService,
        repo: SessionRepository,
        password_reset_repo: PasswordResetTokenRepository,
        email_verification_repo: EmailVerificationTokenRepository,
    ) -> None:
        self.user_service = user_service
        self.repo = repo
        self.password_reset_repo = password_reset_repo
        self.email_verification_repo = email_verification_repo

        self.providers = {name: cls() for name, cls in OAUTH_PROVIDERS.items()}

    @staticmethod
    def generate_session_id() -> str:
        return f"s_{secrets.token_urlsafe(64)}"

    @staticmethod
    def generate_token(prefix: str = "t") -> str:
        """Generate a secure random token with a prefix."""
        return f"{prefix}_{secrets.token_urlsafe(32)}"

    async def _create_session_for_user(self, user_id: uuid.UUID) -> SessionResponse:
        """Create a new session for the given user and return the session response."""
        created_session = await self.repo.create(
            TokenCreate(
                id=self.generate_session_id(),
                user_id=user_id,
                expires_at=datetime.now(UTC) + timedelta(days=365),
            )
        )
        return SessionResponse(
            id=created_session.id,
            expires_at=created_session.expires_at,
        )

    async def authenticate(self, email: str, password: str) -> SessionResponse:
        user = await self.user_service.authenticate(email=email, password=password)
        return await self._create_session_for_user(user.id)

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
            raise UnsupportedOAuthProviderError()

        oauth_user = await provider.callback(payload)
        if not oauth_user.email_verified:
            # An unverified provider email proves nothing; never link it.
            raise OAuthProviderError()
        user = await self.user_service.find_or_create_by_email(
            oauth_user.email,
            UserCreate(
                email=oauth_user.email,
                display_name=oauth_user.display_name or "",
            ),
        )
        if not user.is_active:
            raise InactiveUserError()
        if user.email_verified_at is None:
            if user.password is not None:
                # Anyone could have registered this unverified email with a
                # password. The provider proved the real owner, so the old
                # password and its sessions must not keep access.
                await self.user_service.clear_password(user.id)
                await self.logout_all(user.id)
            await self.user_service.mark_email_verified(user.id)
        return await self._create_session_for_user(user.id)

    async def validate_session(self, session_id: str) -> User:
        session = await self.repo.get_by_field(
            "id", session_id, response_model=UserSessionResponse, raise_error=True
        )
        if session.expires_at < datetime.now(UTC):
            raise SessionExpiredError()
        user = session.user
        if not user.is_active:
            raise InactiveUserError()
        return user

    async def logout(self, session_id: str) -> None:
        """Invalidate a session by deleting it."""
        await self.repo.delete_session(session_id)

    async def logout_all(self, user_id: uuid.UUID) -> None:
        """Invalidate all sessions for a user (logout from all devices)."""
        await self.repo.delete_all_for_user(user_id)

    # Password Reset Methods

    async def initiate_password_reset(self, email: str) -> str | None:
        """
        Initiate password reset process.

        Returns the token if successful (for sending via email).
        Returns None if user not found (to prevent email enumeration).
        Raises OAuthUserPasswordResetError if user is OAuth-only.
        """
        user = await self.user_service.get_by_field("email", email, raise_error=False)
        if not user:
            # Prevent email enumeration: return None rather than raising
            return None

        if user.password is None:
            raise OAuthUserPasswordResetError()

        await self.password_reset_repo.invalidate_user_tokens(user.id)

        token = self.generate_token("pr")
        await self.password_reset_repo.create(
            TokenCreate(
                id=token,
                user_id=user.id,
                expires_at=datetime.now(UTC)
                + timedelta(hours=PASSWORD_RESET_TOKEN_EXPIRY_HOURS),
            )
        )

        return token

    async def reset_password(self, token: str, new_password: str) -> None:
        """
        Reset password using a valid token.

        Raises InvalidTokenError if token is invalid or expired.
        """
        token_record = await self.password_reset_repo.get_valid_token(token)
        if not token_record:
            raise InvalidTokenError()

        await self.user_service.update_password(token_record.user_id, new_password)
        await self.password_reset_repo.mark_as_used(token)
        # Invalidate all sessions after password change as a security measure
        await self.repo.delete_all_for_user(token_record.user_id)

    # Email Verification Methods

    async def initiate_email_verification(self, user_id: uuid.UUID) -> str:
        """
        Initiate email verification process.

        Returns the token for sending via email.
        Raises UserNotFoundError if user not found.
        Raises EmailAlreadyVerifiedError if already verified.
        """
        user = await self.user_service.get_by_id(user_id, raise_error=False)
        if not user:
            raise UserNotFoundError()

        if user.is_email_verified:
            raise EmailAlreadyVerifiedError()

        await self.email_verification_repo.invalidate_user_tokens(user_id)
        token = self.generate_token("ev")
        await self.email_verification_repo.create(
            TokenCreate(
                id=token,
                user_id=user_id,
                expires_at=datetime.now(UTC)
                + timedelta(hours=EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS),
            )
        )

        return token

    async def verify_email(self, token: str) -> None:
        """
        Verify email using a valid token.

        Raises InvalidTokenError if token is invalid or expired.
        """
        token_record = await self.email_verification_repo.get_valid_token(token)
        if not token_record:
            raise InvalidTokenError()

        await self.user_service.mark_email_verified(token_record.user_id)
        await self.email_verification_repo.mark_as_used(token)
