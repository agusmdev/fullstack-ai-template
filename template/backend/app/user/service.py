"""Module with the User service to serve"""

import uuid
from datetime import datetime
from typing import Any, override

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from pydantic import BaseModel

from app.services.base_crud_service import BaseService
from app.user.auth.exceptions import AuthenticationError, InvalidPasswordError
from app.user.models import User
from app.user.schemas import (
    UserRegister,
    UserResponse,
)

from app.user.repository import UserRepository


_ph = PasswordHasher()


class UserService(BaseService[User]):
    """Service to interact with user collection.

    Args:
        repo (UserRepository): The repository to interact with the user collection
    """

    repo: UserRepository

    def __init__(
        self,
        repo: UserRepository,
    ) -> None:
        self.repo = repo

    @override
    async def create(self, entity: BaseModel, **extra_fields: Any) -> User:
        return await self.repo.create(entity, **extra_fields)

    async def find_or_create(self, field: str, value: str, create_fields: BaseModel) -> User:
        user = await self.repo.get_by_field(field, value, raise_error=False)
        if not user:
            user = await self.create(create_fields)
        return user

    async def register(self, user: UserRegister) -> UserResponse:
        created_user = await self.create(user)
        return UserResponse(
            id=created_user.id,
            email=created_user.email,
            display_name=created_user.display_name,
        )

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.repo.get_by_field("email", email, raise_error=False)
        if not user:
            raise AuthenticationError(
                detail="User does not exist or is not allowed to login"
            )

        try:
            if not user.check_password(password):
                raise InvalidPasswordError()
        except VerifyMismatchError as e:
            raise InvalidPasswordError() from e

        return user

    async def update_password(self, user_id: uuid.UUID, new_password: str) -> None:
        """Update a user's password (hashed with Argon2)."""
        hashed_password = _ph.hash(new_password)
        await self.repo.update(user_id, {"password": hashed_password})

    async def mark_email_verified(self, user_id: uuid.UUID) -> None:
        """Mark a user's email as verified."""
        await self.repo.update(user_id, {"email_verified_at": datetime.now()})
