"""Module with schemas for transforming data from requests and responses"""

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, EmailStr, Field, computed_field

from app.core.optional_model import partial_model
from app.database.mixins import OrmBaseModel
from app.user.models import _ph

# The frontend's register form asks for the same minimum.
PASSWORD_MIN_LENGTH = 8


def normalize_email(email: str) -> str:
    """Return the stored form of an email address: lowercase.

    One account per address, whatever its case: "Ada@Example.com" registers,
    logs in and resets the password of the same account as "ada@example.com".
    """
    return email.lower()


# A valid email address, stored and compared lowercase (see normalize_email).
NormalizedEmail = Annotated[EmailStr, AfterValidator(normalize_email)]


class UserBase(BaseModel):
    email: NormalizedEmail
    display_name: str = ""


class UserCreate(UserBase): ...


class UserRegister(UserBase):
    raw_password: str = Field(exclude=True, min_length=PASSWORD_MIN_LENGTH)

    @computed_field
    def password(self) -> str:
        return _ph.hash(self.raw_password)


@partial_model
class UserUpdate(UserBase): ...


class UserResponse(UserBase, OrmBaseModel):
    id: uuid.UUID
    email_verified_at: datetime | None = None

    @computed_field
    def is_email_verified(self) -> bool:
        return self.email_verified_at is not None
