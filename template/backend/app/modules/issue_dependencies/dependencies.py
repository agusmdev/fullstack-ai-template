"""Dependency factory functions for the IssueDependency module."""

from fastapi import Depends

from app.dependencies import get_repository
from app.modules.issue_dependencies.repository import IssueDependencyRepository
from app.modules.issue_dependencies.service import IssueDependencyService
from app.modules.issues.repository import IssueRepository
from app.modules.teams.dependencies import get_team_service


def get_issue_dependency_service(
    repo: IssueDependencyRepository = Depends(
        get_repository(IssueDependencyRepository)
    ),
    team_service=Depends(get_team_service),
    issue_repo: IssueRepository = Depends(get_repository(IssueRepository)),
) -> IssueDependencyService:
    return IssueDependencyService(
        repo=repo, team_service=team_service, issue_repo=issue_repo
    )
