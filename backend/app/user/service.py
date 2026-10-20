"""Module with the User service to serve"""

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel

from app.services.base_crud_service import BaseService
from app.user.auth.exceptions import AuthenticationError, InvalidPasswordError
from app.user.auth.repository import (
    EmailVerificationTokenRepository,
    PasswordResetTokenRepository,
)
from app.user.models import User, _ph
from app.user.repository import UserRepository
from app.user.schemas import (
    UserCreate,
    UserRegister,
    UserResponse,
    normalize_email,
)


class UserService(BaseService[User]):
    """Service to interact with user collection.

    Args:
        repo (UserRepository): The repository to interact with the user collection
        email_verification_repo: Email verification tokens, ended on email change
        password_reset_repo: Password reset tokens, ended on email change
    """

    repo: UserRepository
    email_verification_repo: EmailVerificationTokenRepository
    password_reset_repo: PasswordResetTokenRepository

    def __init__(
        self,
        repo: UserRepository,
        email_verification_repo: EmailVerificationTokenRepository,
        password_reset_repo: PasswordResetTokenRepository,
    ) -> None:
        self.repo = repo
        self.email_verification_repo = email_verification_repo
        self.password_reset_repo = password_reset_repo

    async def find_or_create(
        self, field: str, value: str, create_fields: BaseModel
    ) -> User:
        user = await self.repo.get_by_field(field, value, raise_error=False)
        if not user:
            user = await self.create(create_fields)
        return user

    async def find_or_create_by_email(
        self, email: str, create_fields: UserCreate
    ) -> User:
        """Find a user by email (any case) or create one with the given fields."""
        return await self.find_or_create("email", normalize_email(email), create_fields)

    async def register(self, user: UserRegister) -> UserResponse:
        created_user = await self.create(user)
        return UserResponse.model_validate(created_user)

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.repo.get_by_field(
            "email", normalize_email(email), raise_error=False
        )
        if not user or not user.is_active:
            raise AuthenticationError(
                detail="User does not exist or is not allowed to login"
            )

        if not user.check_password(password):
            raise InvalidPasswordError()

        return user

    async def update_password(self, user_id: uuid.UUID, new_password: str) -> None:
        """Update a user's password (hashed with Argon2)."""
        hashed_password = _ph.hash(new_password)
        await self.repo.update(user_id, {"password": hashed_password})

    async def update(self, entity_id: uuid.UUID, entity: BaseModel) -> User:
        """Update a user; a new email is not verified until it is confirmed again.

        On an email change, open verification and reset tokens are ended too:
        they were sent to the old address, so they must not prove the new one.
        """
        values = entity.model_dump(exclude_unset=True)
        email_changed = False
        if "email" in values:
            current = await self.repo.get(entity_id)
            if current is not None and current.email != values["email"]:
                values["email_verified_at"] = None
                email_changed = True
        result = await self.repo.update(entity_id, values)
        if email_changed:
            await self.email_verification_repo.invalidate_user_tokens(entity_id)
            await self.password_reset_repo.invalidate_user_tokens(entity_id)
        self._log_entity(entity_id)
        return result

    async def clear_password(self, user_id: uuid.UUID) -> None:
        """Remove a user's password, so only their sign-in provider can log in."""
        await self.repo.update(user_id, {"password": None})

    async def mark_email_verified(self, user_id: uuid.UUID) -> None:
        """Mark a user's email as verified."""
        await self.repo.update(user_id, {"email_verified_at": datetime.now(tz=UTC)})
