"""Cycle service — business logic layer (team-scoped).

Enforces that a user can only read/write cycles for teams they belong to.
Creating/updating/deleting cycles requires the ``member`` role. The date
window (``ends_at > starts_at``) is validated both at the schema layer (422
when both dates are in the payload) and here in the service for partial
updates where only one date is provided (resolved against the stored entity).
"""

import uuid
from datetime import date

from fastapi import HTTPException
from fastapi_filter.base.filter import BaseFilterModel
from fastapi_pagination import Page, Params
from pydantic import BaseModel
from sqlalchemy import select

from app.modules.cycles.models import Cycle
from app.modules.cycles.repository import CycleRepository
from app.modules.teams.models import TeamRole
from app.modules.teams.service import TeamService
from app.repositories.base_repository import QueryOptions
from app.repositories.exceptions import NotFoundError
from app.services.base_crud_service import BaseService


class CycleService(BaseService[Cycle]):
    """Service for Cycle entity with team-membership-based scoping."""

    repo: CycleRepository
    team_service: TeamService

    def __init__(self, repo: CycleRepository, team_service: TeamService) -> None:
        self.repo = repo
        self.team_service = team_service

    # ------------------------------------------------------------------
    # Date-window validation (defense-in-depth)
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_window(starts_at: date, ends_at: date) -> None:
        """Raise 422 when ``ends_at`` is not strictly after ``starts_at``."""
        if ends_at <= starts_at:
            raise HTTPException(
                status_code=422,
                detail="ends_at must be after starts_at",
            )

    # ------------------------------------------------------------------
    # Read (team-scoped)
    # ------------------------------------------------------------------

    async def get_all_paginated(  # type: ignore[override]
        self,
        pagination_params: Params,
        entity_filter: BaseFilterModel | None = None,
        *,
        user_id: uuid.UUID,
        team_id: uuid.UUID | None = None,
    ) -> Page[Cycle]:
        """List cycles for the user's teams.

        If ``team_id`` is provided, the result is restricted to that team
        (the user must be a member, else 404).
        """
        team_ids = await self.team_service.get_team_ids_for_user(user_id)
        if team_id is not None:
            if team_id not in team_ids:
                raise NotFoundError(detail=f"Team '{team_id}' not found")
            team_ids = [team_id]
        base_query = select(Cycle).where(Cycle.team_id.in_(team_ids))
        opts = QueryOptions(base_query=base_query)
        return await self.repo.get_all_paginated(pagination_params, entity_filter, opts)

    async def get_by_id(  # type: ignore[override]
        self, entity_id: uuid.UUID, *, user_id: uuid.UUID
    ) -> Cycle:
        """Get a cycle by ID, enforcing team membership."""
        team_ids = await self.team_service.get_team_ids_for_user(user_id)
        cycle = await self.repo.get(entity_id, raise_error=True)
        if cycle.team_id not in team_ids:
            raise NotFoundError(detail=f"Cycle '{entity_id}' not found")
        return cycle

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def create(  # type: ignore[override]
        self, entity: BaseModel, *, user_id: uuid.UUID
    ) -> Cycle:
        """Create a cycle (member or admin).

        The schema layer already validates ``ends_at > starts_at`` when both
        dates are present (422). This double-checks defensively.
        """
        team_id = getattr(entity, "team_id", None)
        if team_id is None:
            raise NotFoundError(detail="team_id is required")
        await self.team_service.require_team_access(
            user_id, team_id, min_role=TeamRole.member
        )

        starts_at = getattr(entity, "starts_at", None)
        ends_at = getattr(entity, "ends_at", None)
        if starts_at is not None and ends_at is not None:
            self._validate_window(starts_at, ends_at)

        return await self.repo.create(entity)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    async def update(  # type: ignore[override]
        self, entity_id: uuid.UUID, entity: BaseModel, *, user_id: uuid.UUID
    ) -> Cycle:
        """Update a cycle (member or admin of the cycle's team).

        When only one date is provided in a partial update, the resulting
        window is validated against the stored entity's other date.
        """
        cycle = await self.get_by_id(entity_id, user_id=user_id)
        await self.team_service.require_team_access(
            user_id, cycle.team_id, min_role=TeamRole.member
        )

        # Resolve the effective date window (partial vs full update).
        starts_at = getattr(entity, "starts_at", None)
        ends_at = getattr(entity, "ends_at", None)
        effective_start = starts_at if starts_at is not None else cycle.starts_at
        effective_end = ends_at if ends_at is not None else cycle.ends_at
        self._validate_window(effective_start, effective_end)

        return await self.repo.update(entity_id, entity)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def delete(  # type: ignore[override]
        self, entity_id: uuid.UUID, *, user_id: uuid.UUID
    ) -> None:
        """Delete a cycle (member or admin). Issues are detached (SET NULL)."""
        cycle = await self.get_by_id(entity_id, user_id=user_id)
        await self.team_service.require_team_access(
            user_id, cycle.team_id, min_role=TeamRole.member
        )
        await self.repo.delete(entity_id)
