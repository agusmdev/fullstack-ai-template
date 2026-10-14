import uuid
from datetime import UTC, datetime

from pydantic import AwareDatetime, BaseModel, EmailStr, Field, computed_field

from app.database.mixins import OrmBaseModel
from app.user.schemas import PASSWORD_MIN_LENGTH, NormalizedEmail, UserResponse


class TokenBase(OrmBaseModel):
    """Shared shape of sessions, password reset and email verification tokens."""

    id: str
    # Timezone-aware (UTC), like every other timestamp of the API.
    expires_at: AwareDatetime


class TokenCreate(TokenBase):
    user_id: uuid.UUID


class SessionResponse(TokenBase):
    @computed_field
    def expires_in(self) -> int:
        return int((self.expires_at - datetime.now(UTC)).total_seconds())


class SessionUser(UserResponse):
    """User fields loaded with a session; ``is_active`` stays out of UserResponse."""

    is_active: bool


class UserSessionResponse(SessionResponse):
    user: SessionUser


class OAuthCallback(BaseModel):
    # Absent when the provider reports an error (e.g. ?error=access_denied).
    code: str | None = None
    state: str | None = None

    redirect_url: str | None = None

    error: str | None = None
    error_description: str | None = None
    error_uri: str | None = None

    access_token: str | None = None
    token_type: str | None = None
    expires_in: int | None = None
    refresh_token: str | None = None

    scope: str | None = None


class OAuthUser(BaseModel):
    token: str
    email: EmailStr
    # The provider confirmed that the user owns this email.
    email_verified: bool
    # Optional: some provider accounts have no name.
    display_name: str | None = None


class LogoutResponse(BaseModel):
    status: str = "logged_out"
    message: str = "Successfully logged out"


# Password Reset Schemas
class PasswordResetRequest(BaseModel):
    email: NormalizedEmail


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=PASSWORD_MIN_LENGTH)


class PasswordResetResponse(BaseModel):
    status: str = "success"
    message: str = "Password reset email sent"


class PasswordResetConfirmResponse(BaseModel):
    status: str = "success"
    message: str = "Password has been reset successfully"


# Email Verification Schemas
class EmailVerificationConfirm(BaseModel):
    token: str


class EmailVerificationResponse(BaseModel):
    status: str = "success"
    message: str = "Verification email sent"


class EmailVerificationConfirmResponse(BaseModel):
    status: str = "success"
    message: str = "Email has been verified successfully"
