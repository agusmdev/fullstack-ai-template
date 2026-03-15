import uuid
from datetime import datetime

from sqlalchemy import delete, select, update

from app.repositories.sql_repository import SQLAlchemyRepository
from app.user.auth.models import EmailVerificationToken, PasswordResetToken, Session


class SessionRepository(SQLAlchemyRepository[Session]):
    model = Session

    async def delete(self, session_id: str) -> None:  # type: ignore[override]
        """Delete a session by its string ID (overrides base delete with str instead of UUID)."""
        await self._session.execute(delete(Session).where(Session.id == session_id))
        await self._session.commit()

    async def delete_all_for_user(self, user_id: uuid.UUID) -> None:
        """Delete all sessions for a user (logout from all devices)."""
        await self._session.execute(delete(Session).where(Session.user_id == user_id))
        await self._session.commit()


class PasswordResetTokenRepository(SQLAlchemyRepository[PasswordResetToken]):
    model = PasswordResetToken

    async def get_valid_token(self, token_id: str) -> PasswordResetToken | None:
        """Get a valid (unexpired, unused) password reset token."""
        result = await self._session.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.id == token_id,
                PasswordResetToken.expires_at > datetime.now(),
                PasswordResetToken.used_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def mark_as_used(self, token_id: str) -> None:
        """Mark a token as used."""
        await self._session.execute(
            update(PasswordResetToken)
            .where(PasswordResetToken.id == token_id)
            .values(used_at=datetime.now())
        )
        await self._session.commit()

    async def invalidate_user_tokens(self, user_id: uuid.UUID) -> None:
        """Invalidate all password reset tokens for a user."""
        await self._session.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.used_at.is_(None),
            )
            .values(used_at=datetime.now())
        )
        await self._session.commit()


class EmailVerificationTokenRepository(SQLAlchemyRepository[EmailVerificationToken]):
    model = EmailVerificationToken

    async def get_valid_token(self, token_id: str) -> EmailVerificationToken | None:
        """Get a valid (unexpired, unused) email verification token."""
        result = await self._session.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.id == token_id,
                EmailVerificationToken.expires_at > datetime.now(),
                EmailVerificationToken.used_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def mark_as_used(self, token_id: str) -> None:
        """Mark a token as used."""
        await self._session.execute(
            update(EmailVerificationToken)
            .where(EmailVerificationToken.id == token_id)
            .values(used_at=datetime.now())
        )
        await self._session.commit()

    async def invalidate_user_tokens(self, user_id: uuid.UUID) -> None:
        """Invalidate all email verification tokens for a user."""
        await self._session.execute(
            update(EmailVerificationToken)
            .where(
                EmailVerificationToken.user_id == user_id,
                EmailVerificationToken.used_at.is_(None),
            )
            .values(used_at=datetime.now())
        )
        await self._session.commit()
