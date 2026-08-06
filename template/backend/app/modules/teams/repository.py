"""Team and TeamMembership repositories — data access layer."""

from app.modules.teams.models import Team, TeamMembership
from app.repositories.sql_repository import SQLAlchemyRepository


class TeamRepository(SQLAlchemyRepository[Team]):
    """Repository for Team entity."""

    model = Team


class TeamMembershipRepository(SQLAlchemyRepository[TeamMembership]):
    """Repository for TeamMembership entity."""

    model = TeamMembership
