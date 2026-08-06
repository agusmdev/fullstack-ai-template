"""Direct tests for module-level dependency factory functions.

These cover the dependency wiring declared in app/modules/teams/dependencies.py,
app/user/dependencies.py, and app/user/auth/dependencies.py — previously only
exercised transitively.
"""

from unittest.mock import MagicMock

from app.modules.teams.dependencies import get_team_service
from app.modules.teams.service import TeamService
from app.user.auth.dependencies import get_auth_service
from app.user.auth.service import AuthService
from app.user.dependencies import get_user_service
from app.user.service import UserService


class TestGetTeamService:
    def test_returns_team_service_bound_to_repos(self):
        repo = MagicMock(name="TeamRepository")
        membership_repo = MagicMock(name="TeamMembershipRepository")

        service = get_team_service(repo=repo, membership_repo=membership_repo)

        assert isinstance(service, TeamService)
        assert service.repo is repo
        assert service.membership_repo is membership_repo


class TestGetUserService:
    def test_returns_user_service_bound_to_repo(self):
        repo = MagicMock(name="UserRepository")

        service = get_user_service(repo=repo)

        assert isinstance(service, UserService)
        assert service.repo is repo


class TestGetAuthService:
    def test_returns_auth_service_with_all_repos(self):
        session_repo = MagicMock(name="SessionRepository")
        password_reset_repo = MagicMock(name="PasswordResetTokenRepository")
        email_verification_repo = MagicMock(name="EmailVerificationTokenRepository")
        user_service = MagicMock(spec=UserService)

        service = get_auth_service(
            session_repo=session_repo,
            password_reset_repo=password_reset_repo,
            email_verification_repo=email_verification_repo,
            user_service=user_service,
        )

        assert isinstance(service, AuthService)
        assert service.repo is session_repo
        assert service.password_reset_repo is password_reset_repo
        assert service.email_verification_repo is email_verification_repo
        assert service.user_service is user_service
        assert service.team_service is not None
