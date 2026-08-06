"""Dependency factory functions for the Issue module."""

from fastapi import Depends

from app.dependencies import get_repository
from app.modules.issues.repository import IssueRepository
from app.modules.issues.service import IssueService
from app.modules.teams.dependencies import get_team_service
from app.modules.workflows.repository import WorkflowStateRepository


def get_issue_service(
    repo: IssueRepository = Depends(get_repository(IssueRepository)),
    team_service=Depends(get_team_service),
    workflow_state_repo: WorkflowStateRepository = Depends(
        get_repository(WorkflowStateRepository)
    ),
) -> IssueService:
    return IssueService(
        repo=repo,
        team_service=team_service,
        workflow_state_repo=workflow_state_repo,
    )
