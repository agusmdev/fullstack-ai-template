"""Dependency factory functions for the Activity module."""

from fastapi import Depends

from app.dependencies import get_repository
from app.modules.activity.repository import ActivityRepository
from app.modules.activity.service import ActivityService
from app.modules.issues.repository import IssueRepository
from app.modules.teams.dependencies import get_team_service


def get_activity_service(
    repo: ActivityRepository = Depends(get_repository(ActivityRepository)),
    team_service=Depends(get_team_service),
    issue_repo: IssueRepository = Depends(get_repository(IssueRepository)),
) -> ActivityService:
    return ActivityService(repo=repo, team_service=team_service, issue_repo=issue_repo)
