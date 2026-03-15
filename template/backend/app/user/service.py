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

from .repository import UserRepository

# The UserRepository.get method accepts str for email lookups
# which is a narrowing of the base UUID type.


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

    async def get(
        self,
        entity_id: str | uuid.UUID,
        filter_field: str = "id",
        raise_error: bool = True,
    ) -> User | None:
        """Get a user by ID or other field."""
        return await self.repo.get(
            entity_id, raise_error=raise_error, filter_field=filter_field
        )

    @override
    async def create(self, entity: BaseModel, **extra_fields: Any) -> User:
        return await self.repo.create(entity, **extra_fields)

    async def get_or_create(
        self, user_id: str, create_fields: BaseModel, filter_field: str = "id"
    ) -> User:
        user = await self.repo.get(
            user_id, raise_error=False, filter_field=filter_field
        )
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
        user = await self.repo.get(email, raise_error=False, filter_field="email")
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
        ph = PasswordHasher()
        hashed_password = ph.hash(new_password)
        await self.repo.update(user_id, {"password": hashed_password})

    async def mark_email_verified(self, user_id: uuid.UUID) -> None:
        """Mark a user's email as verified."""
        await self.repo.update(user_id, {"email_verified_at": datetime.now()})
