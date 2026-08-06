"""Dependency factory functions for the Team module."""

from fastapi import Depends

from app.dependencies import get_repository
from app.modules.teams.repository import TeamMembershipRepository, TeamRepository
from app.modules.teams.service import TeamService


def get_team_service(
    repo: TeamRepository = Depends(get_repository(TeamRepository)),
    membership_repo: TeamMembershipRepository = Depends(
        get_repository(TeamMembershipRepository)
    ),
) -> TeamService:
    return TeamService(repo=repo, membership_repo=membership_repo)
