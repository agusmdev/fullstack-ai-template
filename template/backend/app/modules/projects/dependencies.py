"""Dependency factory functions for the Project module."""

from fastapi import Depends

from app.dependencies import get_repository
from app.modules.projects.repository import ProjectRepository
from app.modules.projects.service import ProjectService
from app.modules.teams.dependencies import get_team_service


def get_project_service(
    repo: ProjectRepository = Depends(get_repository(ProjectRepository)),
    team_service=Depends(get_team_service),
) -> ProjectService:
    return ProjectService(repo=repo, team_service=team_service)
