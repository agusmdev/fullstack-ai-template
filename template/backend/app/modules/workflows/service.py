"""WorkflowState service — business logic layer (team-scoped).

Enforces that a user can only read/write workflow states for teams they belong
to, and that mutating workflow states requires the ``admin`` role. Read access
(scoping) reuses ``TeamService`` membership helpers.
"""

import uuid

from fastapi_filter.base.filter import BaseFilterModel
from fastapi_pagination import Page, Params
from pydantic import BaseModel
from sqlalchemy import select

from app.modules.teams.models import TeamRole
from app.modules.teams.service import TeamService
from app.modules.workflows.models import WorkflowState
from app.modules.workflows.repository import WorkflowStateRepository
from app.repositories.base_repository import QueryOptions
from app.repositories.exceptions import NotFoundError
from app.services.base_crud_service import BaseService


class WorkflowStateService(BaseService[WorkflowState]):
    """Service for WorkflowState entity with team-membership-based scoping."""

    repo: WorkflowStateRepository
    team_service: TeamService

    def __init__(
        self,
        repo: WorkflowStateRepository,
        team_service: TeamService,
    ) -> None:
        self.repo = repo
        self.team_service = team_service

    async def get_all_paginated(  # type: ignore[override]
        self,
        pagination_params: Params,
        entity_filter: BaseFilterModel | None = None,
        *,
        user_id: uuid.UUID,
        team_id: uuid.UUID | None = None,
    ) -> Page[WorkflowState]:
        """List workflow states for the user's teams.

        If ``team_id`` is provided, the result is restricted to that team
        (the user must be a member, else 404).
        """
        team_ids = await self.team_service.get_team_ids_for_user(user_id)
        if team_id is not None:
            if team_id not in team_ids:
                raise NotFoundError(detail=f"Team '{team_id}' not found")
            team_ids = [team_id]
        base_query = select(WorkflowState).where(WorkflowState.team_id.in_(team_ids))
        opts = QueryOptions(base_query=base_query)
        return await self.repo.get_all_paginated(pagination_params, entity_filter, opts)

    async def get_by_id(  # type: ignore[override]
        self, entity_id: uuid.UUID, *, user_id: uuid.UUID
    ) -> WorkflowState:
        """Get a workflow state by ID, enforcing team membership."""
        team_ids = await self.team_service.get_team_ids_for_user(user_id)
        state = await self.repo.get(entity_id, raise_error=True)
        if state.team_id not in team_ids:
            raise NotFoundError(detail=f"WorkflowState '{entity_id}' not found")
        return state

    async def create(  # type: ignore[override]
        self, entity: BaseModel, *, user_id: uuid.UUID
    ) -> WorkflowState:
        """Create a workflow state (admin only)."""
        team_id = getattr(entity, "team_id", None)
        if team_id is None:
            raise NotFoundError(detail="team_id is required")
        await self.team_service.require_team_access(
            user_id, team_id, min_role=TeamRole.admin
        )
        return await self.repo.create(entity)

    async def update(  # type: ignore[override]
        self, entity_id: uuid.UUID, entity: BaseModel, *, user_id: uuid.UUID
    ) -> WorkflowState:
        """Update a workflow state (admin only)."""
        state = await self.get_by_id(entity_id, user_id=user_id)
        await self.team_service.require_team_access(
            user_id, state.team_id, min_role=TeamRole.admin
        )
        return await self.repo.update(entity_id, entity)

    async def delete(  # type: ignore[override]
        self, entity_id: uuid.UUID, *, user_id: uuid.UUID
    ) -> None:
        """Delete a workflow state (admin only)."""
        state = await self.get_by_id(entity_id, user_id=user_id)
        await self.team_service.require_team_access(
            user_id, state.team_id, min_role=TeamRole.admin
        )
        await self.repo.delete(entity_id)
