---
name: fastapi-auth
description: Implement session-based authentication in FastAPI applications. Use when building login/logout flows, protecting endpoints with auth dependencies, creating user models with password hashing, managing sessions in database, or implementing auth exceptions. Covers HTTPBearer token validation, Argon2 password hashing, session repository/service patterns, and route protection with dependency injection.
---

# FastAPI Session-Based Authentication

## Architecture Overview

```
Auth Flow: Client → HTTPBearer → AuthService.check_session() → User
OAuth Flow: Google → /oauth/google/callback → AuthService.oauth_login() → Session → Redirect
Layers: Repository (data) → Service (logic) → Router (endpoints) → Dependencies (guards)
```

## User Model

```python
# app/user/models.py
import uuid
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models import TimestampMixin

ph = PasswordHasher()

class User(TimestampMixin, Base):
    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))

    def check_password(self, password: str) -> bool:
        try:
            ph.verify(self.hashed_password, password)
            return True
        except VerifyMismatchError:
            return False

    @staticmethod
    def hash_password(password: str) -> str:
        return ph.hash(password)
```

## Session Model

```python
# app/user/auth/models.py
import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.models import TimestampMixin

class Session(TimestampMixin, Base):
    __tablename__ = "session"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), index=True
    )
    user: Mapped["User"] = relationship()
    expires_at: Mapped[datetime] = mapped_column(index=True)
```

## Auth Exceptions

```python
# app/user/auth/exceptions.py
from app.core.exceptions import HTTPExceptionMixin

class AuthenticationError(HTTPExceptionMixin):
    status_code = 401
    detail = "Authentication failed"
    error_code = "authentication_failed"

class InvalidPasswordError(AuthenticationError):
    detail = "Invalid password"
    error_code = "invalid_password"

class SessionExpiredError(AuthenticationError):
    detail = "Session expired"
    error_code = "session_expired"
```

## OAuth Schemas

```python
# app/user/auth/schemas.py
from datetime import datetime
from pydantic import BaseModel, EmailStr, computed_field

class SessionResponse(BaseModel):
    id: str
    expires_at: datetime

    @computed_field
    def expires_in(self) -> int:
        return int((self.expires_at - datetime.now()).total_seconds())

class UserSessionResponse(SessionResponse):
    user: "UserResponse"

class OAuthCallback(BaseModel):
    """OAuth callback query parameters from provider."""
    code: str
    state: str | None = None
    redirect_url: str | None = None
    error: str | None = None
    error_description: str | None = None

class OAuthUser(BaseModel):
    """User info extracted from OAuth provider."""
    token: str
    email: EmailStr
    display_name: str
```

## Google OAuth Provider

```python
# app/user/auth/service.py
from requests_oauthlib import OAuth2Session
from app.core.config import settings
from app.user.auth.schemas import OAuthCallback, OAuthUser

class GoogleOAuth:
    """Google OAuth2 provider implementation."""

    def callback(self, callback: OAuthCallback) -> OAuthUser:
        """Exchange authorization code for user info."""
        google = OAuth2Session(
            client_id=settings.GOOGLE_CLIENT_ID,
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
            state=callback.state,
            scope="https://www.googleapis.com/auth/userinfo.profile openid https://www.googleapis.com/auth/userinfo.email",
        )

        # Exchange code for access token
        token = google.fetch_token(
            "https://oauth2.googleapis.com/token",
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            code=callback.code,
        )

        # Fetch user info from Google API
        user_info_response = google.get(settings.GOOGLE_USER_INFO_URL)
        user_info = user_info_response.json()

        return OAuthUser(
            token=token["access_token"],
            email=user_info.get("email"),
            display_name=user_info.get("name"),
        )
```

## Auth Service with OAuth

```python
# app/user/auth/service.py
import secrets
from datetime import datetime, timedelta
from injector import Inject

from app.user.auth.exceptions import SessionExpiredError
from app.user.auth.repository import SessionRepository
from app.user.auth.schemas import OAuthCallback, SessionResponse, UserSessionResponse
from app.user.schemas import UserCreate
from app.user.service import UserService

class AuthService:
    def __init__(
        self,
        user_service: Inject[UserService],
        session_repository: Inject[SessionRepository],
    ):
        self.user_service = user_service
        self.session_repository = session_repository
        self.providers = {"google": GoogleOAuth()}

    @staticmethod
    def session_id() -> str:
        return f"s_{secrets.token_urlsafe(64)}"

    def authenticate(self, email: str, password: str) -> SessionResponse:
        """Login with email/password."""
        user = self.user_service.authenticate(email=email, password=password)
        return self._create_session(user.id)

    def register(self, new_user) -> SessionResponse:
        """Register and auto-login."""
        self.user_service.register(user=new_user)
        return self.authenticate(email=new_user.email, password=new_user.raw_password)

    def oauth_login(self, provider_name: str, payload: OAuthCallback) -> SessionResponse:
        """Handle OAuth callback and create session."""
        provider = self.providers.get(provider_name)
        if not provider:
            raise ValueError("Unsupported provider")

        # Get user info from OAuth provider
        oauth_user = provider.callback(payload)

        # Get or create user by email
        user = self.user_service.get_or_create(
            oauth_user.email,
            filter_field="email",
            create_fields=UserCreate(
                email=oauth_user.email,
                display_name=oauth_user.display_name or "",
            ),
        )

        return self._create_session(user.id)

    def _create_session(self, user_id) -> SessionResponse:
        """Create session for user."""
        session = self.session_repository.save(
            Session(
                id=self.session_id(),
                user_id=user_id,
                expires_at=datetime.now() + timedelta(days=365),
            )
        )
        return SessionResponse(id=session.id, expires_at=session.expires_at)

    def check_session(self, session_id: str) -> UserSessionResponse:
        """Validate session token."""
        session = self.session_repository.get_with_user(session_id)
        if not session or session.expires_at < datetime.now():
            raise SessionExpiredError()
        return UserSessionResponse(user=session.user, expires_at=session.expires_at)
```

## OAuth Configuration

```python
# app/core/config.py
from pydantic import computed_field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/oauth/google/callback"
    GOOGLE_USER_INFO_URL: str = "https://www.googleapis.com/oauth2/v1/userinfo"

    # Frontend URL for redirects
    FRONTEND_URL: str = "http://localhost:3000"

    @computed_field
    def GOOGLE_OAUTH_ENABLED(self) -> bool:
        return bool(self.GOOGLE_CLIENT_ID) and bool(self.GOOGLE_CLIENT_SECRET)

settings = Settings()
```

## OAuth Router

```python
# app/user/auth/routers.py
import loguru
from fastapi import APIRouter, Body, Query, status
from fastapi.responses import RedirectResponse
from fastapi_injector import Injected

from app.core.config import settings
from app.user.auth.schemas import OAuthCallback, SessionResponse
from app.user.auth.service import AuthService
from app.user.schemas import UserRegister

auth_router = APIRouter()

@auth_router.post("/login", status_code=status.HTTP_200_OK)
def login_user(
    email: str = Body(...),
    password: str = Body(...),
    auth_service: AuthService = Injected(AuthService),
) -> SessionResponse:
    return auth_service.authenticate(email=email, password=password)

@auth_router.post("/register")
def register_user(
    user: UserRegister = Body(...),
    auth_service: AuthService = Injected(AuthService),
) -> SessionResponse:
    return auth_service.register(new_user=user)

@auth_router.get("/oauth/{provider}/callback")
def oauth_callback(
    provider: str,
    auth_service: AuthService = Injected(AuthService),
    callback: OAuthCallback = Query(...),
) -> RedirectResponse:
    """Handle OAuth provider callback."""
    try:
        session = auth_service.oauth_login(provider_name=provider, payload=callback)

        # Redirect to frontend with session token
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/oauth/callback?session={session.id}",
            status_code=status.HTTP_302_FOUND,
        )
    except Exception as e:
        loguru.logger.exception(e)
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/oauth/error?error={str(e)}",
            status_code=status.HTTP_302_FOUND,
        )
```

## Session Repository

```python
# app/user/auth/repository.py
from sqlalchemy.orm import joinedload

from app.core.repository import SQLAlchemyRepository
from app.user.auth.models import Session

class SessionRepository(SQLAlchemyRepository[Session]):
    model = Session

    def get_with_user(self, session_id: str) -> Session | None:
        return (
            self.session.query(Session)
            .options(joinedload(Session.user))
            .filter(Session.id == session_id)
            .first()
        )
```

## Auth Dependencies (Route Protection)

```python
# app/core/permissions/auth.py
import uuid
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from injector import Injector

from app.user.auth.service import AuthService
from app.user.models import User

http_bearer = HTTPBearer(auto_error=True)

class AuthenticatedUser:
    """Dependency class for protecting routes."""

    @classmethod
    def current_user_id(
        cls,
        request: Request,
        http_auth: HTTPAuthorizationCredentials = Depends(http_bearer),
    ) -> uuid.UUID:
        user = cls._get_user_from_request(request, http_auth)
        return user.id

    @classmethod
    def get_user(
        cls,
        request: Request,
        http_auth: HTTPAuthorizationCredentials = Depends(http_bearer),
    ) -> User:
        return cls._get_user_from_request(request, http_auth)

    @classmethod
    def _get_user_from_request(
        cls,
        request: Request,
        http_auth: HTTPAuthorizationCredentials,
    ) -> User:
        if hasattr(request.state, "user") and request.state.user:
            return request.state.user

        injector: Injector = request.state.injector
        auth_service = injector.get(AuthService)
        session_response = auth_service.check_session(http_auth.credentials)
        request.state.user = session_response.user
        return session_response.user
```

## Protecting Routes

```python
# app/routers.py
from fastapi import APIRouter, Depends
from app.core.permissions.auth import AuthenticatedUser

router = APIRouter()

# Protected routes
router.include_router(
    user_router,
    prefix="/users",
    dependencies=[Depends(AuthenticatedUser.current_user_id)]
)

# Public routes
router.include_router(auth_router, prefix="/auth")
```

## User Service

```python
# app/user/service.py
from injector import Inject
from app.user.auth.exceptions import AuthenticationError, InvalidPasswordError
from app.user.models import User
from app.user.repository import UserRepository

class UserService:
    def __init__(self, user_repository: Inject[UserRepository]):
        self.user_repository = user_repository

    def authenticate(self, email: str, password: str) -> User:
        user = self.user_repository.get_by_email(email)
        if not user:
            raise AuthenticationError()
        if not user.check_password(password):
            raise InvalidPasswordError()
        return user

    def get_or_create(self, value, filter_field: str, create_fields) -> User:
        """Get existing user or create new one (for OAuth)."""
        user = self.user_repository.get_by_field(filter_field, value)
        if user:
            return user
        return self.user_repository.save(User(**create_fields.model_dump()))
```

## Google OAuth Flow

```
1. Frontend redirects to Google consent screen:
   https://accounts.google.com/o/oauth2/v2/auth?
     client_id={GOOGLE_CLIENT_ID}&
     redirect_uri={GOOGLE_REDIRECT_URI}&
     response_type=code&
     scope=openid email profile&
     state={random_state}

2. User authorizes, Google redirects to:
   /auth/oauth/google/callback?code={auth_code}&state={state}

3. Backend exchanges code for token via GoogleOAuth.callback()

4. Backend fetches user info from Google API

5. Backend creates/gets user, creates session

6. Backend redirects to frontend:
   {FRONTEND_URL}/oauth/callback?session={session_id}

7. Frontend stores session token in localStorage
```

## Key Patterns

1. **Session tokens**: Prefix with `s_` + 64-char URL-safe base64
2. **Password hashing**: Argon2 via `User.hash_password()`
3. **Request caching**: Store user in `request.state.user`
4. **HTTPBearer**: Use `auto_error=True` for automatic 401
5. **OAuth providers**: Registry pattern in `self.providers` dict
6. **OAuth user creation**: `get_or_create()` to handle returning users
7. **Frontend redirect**: Pass session ID via query param after OAuth
