"""Dependency factory functions for the WorkflowState module."""

from fastapi import Depends

from app.dependencies import get_repository
from app.modules.teams.dependencies import get_team_service
from app.modules.workflows.repository import WorkflowStateRepository
from app.modules.workflows.service import WorkflowStateService


def get_workflow_state_service(
    repo: WorkflowStateRepository = Depends(get_repository(WorkflowStateRepository)),
    team_service=Depends(get_team_service),
) -> WorkflowStateService:
    return WorkflowStateService(repo=repo, team_service=team_service)
