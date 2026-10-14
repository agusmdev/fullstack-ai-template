"""Dependency factory functions for User module.

Auth DI lives in app/user/auth/dependencies.py so the auth package owns its
full DI surface.
"""

from fastapi import Depends

from app.dependencies import get_repository
from app.user.auth.repository import (
    EmailVerificationTokenRepository,
    PasswordResetTokenRepository,
)
from app.user.repository import UserRepository
from app.user.service import UserService


def get_user_service(
    repo: UserRepository = Depends(get_repository(UserRepository)),
    email_verification_repo: EmailVerificationTokenRepository = Depends(
        get_repository(EmailVerificationTokenRepository)
    ),
    password_reset_repo: PasswordResetTokenRepository = Depends(
        get_repository(PasswordResetTokenRepository)
    ),
) -> UserService:
    return UserService(
        repo=repo,
        email_verification_repo=email_verification_repo,
        password_reset_repo=password_reset_repo,
    )
