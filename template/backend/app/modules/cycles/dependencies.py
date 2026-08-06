"""Dependency factory functions for the Cycle module."""

from fastapi import Depends

from app.dependencies import get_repository
from app.modules.cycles.repository import CycleRepository
from app.modules.cycles.service import CycleService
from app.modules.teams.dependencies import get_team_service


def get_cycle_service(
    repo: CycleRepository = Depends(get_repository(CycleRepository)),
    team_service=Depends(get_team_service),
) -> CycleService:
    return CycleService(repo=repo, team_service=team_service)
