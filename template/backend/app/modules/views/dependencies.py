"""Dependency factory functions for the View module."""

from fastapi import Depends

from app.dependencies import get_repository
from app.modules.teams.dependencies import get_team_service
from app.modules.views.repository import ViewRepository
from app.modules.views.service import ViewService


def get_view_service(
    repo: ViewRepository = Depends(get_repository(ViewRepository)),
    team_service=Depends(get_team_service),
) -> ViewService:
    return ViewService(repo=repo, team_service=team_service)
