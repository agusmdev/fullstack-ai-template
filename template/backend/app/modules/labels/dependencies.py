"""Dependency factory functions for the Label module."""

from fastapi import Depends

from app.dependencies import get_repository
from app.modules.labels.repository import LabelRepository
from app.modules.labels.service import LabelService
from app.modules.teams.dependencies import get_team_service


def get_label_service(
    repo: LabelRepository = Depends(get_repository(LabelRepository)),
    team_service=Depends(get_team_service),
) -> LabelService:
    return LabelService(repo=repo, team_service=team_service)
