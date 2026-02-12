"""Dependency factory functions for User module."""

from fastapi import Depends

from app.dependencies import get_repository
from app.user.auth.repository import (
    EmailVerificationTokenRepository,
    PasswordResetTokenRepository,
    SessionRepository,
)
from app.user.auth.service import AuthService
from app.user.repository import UserRepository
from app.user.service import UserService


def get_user_service(
    repo: UserRepository = Depends(get_repository(UserRepository)),
) -> UserService:
    """Factory function to get UserService instance.

    Args:
        repo: The UserRepository instance (injected via Depends)

    Returns:
        UserService: A service instance with the repository injected
    """
    return UserService(repo=repo)


def get_auth_service(
    session_repo: SessionRepository = Depends(get_repository(SessionRepository)),
    password_reset_repo: PasswordResetTokenRepository = Depends(
        get_repository(PasswordResetTokenRepository)
    ),
    email_verification_repo: EmailVerificationTokenRepository = Depends(
        get_repository(EmailVerificationTokenRepository)
    ),
    user_service: UserService = Depends(get_user_service),
) -> AuthService:
    """Factory function to get AuthService instance.

    Args:
        session_repo: The SessionRepository instance (injected via Depends)
        password_reset_repo: The PasswordResetTokenRepository instance
        email_verification_repo: The EmailVerificationTokenRepository instance
        user_service: The UserService instance (injected via Depends)

    Returns:
        AuthService: A service instance with dependencies injected
    """
    return AuthService(
        user_service=user_service,
        repo=session_repo,
        password_reset_repo=password_reset_repo,
        email_verification_repo=email_verification_repo,
    )
