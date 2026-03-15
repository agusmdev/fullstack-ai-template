import uuid
from datetime import datetime
from typing import Generic, TypeVar

from sqlalchemy import delete, select, update

from app.repositories.sql_repository import SQLAlchemyRepository
from app.user.auth.models import EmailVerificationToken, PasswordResetToken, Session

T_Token = TypeVar("T_Token", PasswordResetToken, EmailVerificationToken)


class SessionRepository(SQLAlchemyRepository[Session]):
    model = Session

    async def delete_session(self, session_id: str) -> None:
        """Delete a session by its string ID."""
        await self._session.execute(delete(Session).where(Session.id == session_id))
        await self._session.commit()

    async def delete_all_for_user(self, user_id: uuid.UUID) -> None:
        """Delete all sessions for a user (logout from all devices)."""
        await self._session.execute(delete(Session).where(Session.user_id == user_id))
        await self._session.commit()


class _TokenRepository(SQLAlchemyRepository[T_Token], Generic[T_Token]):  # noqa: UP046
    """Base repository for time-limited, single-use tokens (password reset, email verification).

    Both token types share identical validation, mark-as-used, and invalidation logic.
    Subclasses provide only the concrete model via the class-level `model` attribute.
    """

    async def get_valid_token(self, token_id: str) -> T_Token | None:
        """Return the token if it exists, has not expired, and has not been used."""
        model = self.model  # type: ignore[attr-defined]
        result = await self._session.execute(
            select(model).where(
                model.id == token_id,
                model.expires_at > datetime.now(),
                model.used_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def mark_as_used(self, token_id: str) -> None:
        """Stamp `used_at` on the token, permanently invalidating it."""
        model = self.model  # type: ignore[attr-defined]
        await self._session.execute(
            update(model).where(model.id == token_id).values(used_at=datetime.now())
        )
        await self._session.commit()

    async def invalidate_user_tokens(self, user_id: uuid.UUID) -> None:
        """Invalidate all unused tokens for the given user."""
        model = self.model  # type: ignore[attr-defined]
        await self._session.execute(
            update(model)
            .where(model.user_id == user_id, model.used_at.is_(None))
            .values(used_at=datetime.now())
        )
        await self._session.commit()


class PasswordResetTokenRepository(_TokenRepository[PasswordResetToken]):
    model = PasswordResetToken


class EmailVerificationTokenRepository(_TokenRepository[EmailVerificationToken]):
    model = EmailVerificationToken
