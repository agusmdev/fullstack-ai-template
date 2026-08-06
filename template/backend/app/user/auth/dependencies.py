"""Dependency factory functions for the auth package.

The auth package owns its full DI surface (service factory + auth-internal
repository wiring) so it is self-contained, honoring the public-boundary
contract documented in app/user/auth/__init__.py.
"""

from fastapi import Depends

from app.dependencies import get_repository
from app.user.auth.repository import (
    EmailVerificationTokenRepository,
    PasswordResetTokenRepository,
    SessionRepository,
)
from app.user.auth.service import AuthService
from app.user.dependencies import get_user_service
from app.user.service import UserService


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
    # Lazy import to avoid a circular dependency: app.user.auth is imported by
    # app.modules.teams.routers, so importing teams at module level here would cycle.
    from app.modules.teams.repository import TeamMembershipRepository, TeamRepository
    from app.modules.teams.service import TeamService

    session = session_repo._session
    team_service = TeamService(
        repo=TeamRepository(session),
        membership_repo=TeamMembershipRepository(session),
    )

    return AuthService(
        user_service=user_service,
        repo=session_repo,
        password_reset_repo=password_reset_repo,
        email_verification_repo=email_verification_repo,
        team_service=team_service,
    )
