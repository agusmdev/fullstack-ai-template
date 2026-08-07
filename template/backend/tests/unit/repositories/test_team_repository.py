"""Tests for TeamRepository and TeamMembershipRepository."""

from app.modules.teams.models import Team, TeamMembership
from app.modules.teams.repository import TeamMembershipRepository, TeamRepository


class TestTeamRepositoryModel:
    def test_model_is_team(self, mock_session):
        repo = TeamRepository(session=mock_session)
        assert repo.model is Team


class TestTeamRepositoryInheritance:
    def test_inherits_from_sqlalchemy_repository(self):
        from app.repositories.sql_repository import SQLAlchemyRepository

        assert issubclass(TeamRepository, SQLAlchemyRepository)

    def test_has_crud_methods(self, mock_session):
        repo = TeamRepository(session=mock_session)
        assert hasattr(repo, "get")
        assert hasattr(repo, "create")
        assert hasattr(repo, "update")
        assert hasattr(repo, "delete")


class TestTeamMembershipRepositoryModel:
    def test_model_is_team_membership(self, mock_session):
        repo = TeamMembershipRepository(session=mock_session)
        assert repo.model is TeamMembership

    def test_inherits_from_sqlalchemy_repository(self):
        from app.repositories.sql_repository import SQLAlchemyRepository

        assert issubclass(TeamMembershipRepository, SQLAlchemyRepository)

    def test_has_crud_methods(self, mock_session):
        repo = TeamMembershipRepository(session=mock_session)
        assert hasattr(repo, "get")
        assert hasattr(repo, "create")
        assert hasattr(repo, "update")
        assert hasattr(repo, "delete")
