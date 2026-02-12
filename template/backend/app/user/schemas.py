"""Module with schemas for transforming data from requests and responses"""

import uuid
from datetime import datetime

from argon2 import PasswordHasher
from pydantic import BaseModel, EmailStr, Field, computed_field

from app.core.optional_model import partial_model
from app.database.mixins import OrmBaseModel

ph = PasswordHasher()


class UserBase(BaseModel):
    email: EmailStr
    display_name: str = ""


class UserCreate(UserBase): ...


class UserRegister(UserBase):
    raw_password: str = Field(exclude=True)

    @computed_field
    def password(self) -> str:
        return ph.hash(self.raw_password)


@partial_model
class UserUpdate(UserBase): ...


class UserResponse(UserBase, OrmBaseModel):
    id: uuid.UUID
    email_verified_at: datetime | None = None

    @computed_field
    def is_email_verified(self) -> bool:
        return self.email_verified_at is not None
