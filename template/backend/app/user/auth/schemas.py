import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, computed_field

from app.database.mixins import OrmBaseModel
from app.user.schemas import UserResponse


class SessionBase(OrmBaseModel):
    id: str
    expires_at: datetime


class SessionResponse(SessionBase):
    @computed_field
    def expires_in(self) -> int:
        return int((self.expires_at - datetime.now()).total_seconds())


class SessionCreate(SessionBase):
    user_id: uuid.UUID


class UserSessionResponse(SessionResponse):
    user: UserResponse


class OAuthCallback(BaseModel):
    code: str
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
    display_name: str


class LogoutResponse(BaseModel):
    status: str = "logged_out"
    message: str = "Successfully logged out"


# Password Reset Schemas
class PasswordResetTokenBase(OrmBaseModel):
    id: str
    expires_at: datetime


class PasswordResetTokenCreate(PasswordResetTokenBase):
    user_id: uuid.UUID


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class PasswordResetResponse(BaseModel):
    status: str = "success"
    message: str = "Password reset email sent"


class PasswordResetConfirmResponse(BaseModel):
    status: str = "success"
    message: str = "Password has been reset successfully"


# Email Verification Schemas
class EmailVerificationTokenBase(OrmBaseModel):
    id: str
    expires_at: datetime


class EmailVerificationTokenCreate(EmailVerificationTokenBase):
    user_id: uuid.UUID


class EmailVerificationRequest(BaseModel):
    pass


class EmailVerificationConfirm(BaseModel):
    token: str


class EmailVerificationResponse(BaseModel):
    status: str = "success"
    message: str = "Verification email sent"


class EmailVerificationConfirmResponse(BaseModel):
    status: str = "success"
    message: str = "Email has been verified successfully"
