"""View service — business logic layer (team-scoped, member-write).

A saved View captures the Issues/Board view configuration (filters + group_by +
order_by) for a team. It is scoped to the user's team membership: a user can
list/read views for their teams and create/update/delete views with the
``member`` role. The owner (creator) is recorded on create for attribution but
team membership governs access (any team member can see/use a team's saved
views).
"""

import uuid

from fastapi_filter.base.filter import BaseFilterModel
from fastapi_pagination import Page, Params
from pydantic import BaseModel
from sqlalchemy import select

from app.modules.teams.models import TeamRole
from app.modules.teams.service import TeamService
from app.modules.views.models import View
from app.modules.views.repository import ViewRepository
from app.repositories.base_repository import QueryOptions
from app.repositories.exceptions import NotFoundError
from app.services.base_crud_service import BaseService


class ViewService(BaseService[View]):
    """Service for View entity with team-membership-based scoping."""

    repo: ViewRepository
    team_service: TeamService

    def __init__(self, repo: ViewRepository, team_service: TeamService) -> None:
        self.repo = repo
        self.team_service = team_service

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
    ) -> Page[View]:
        """List saved views for the user's teams.

        If ``team_id`` is provided, the result is restricted to that team
        (the user must be a member, else 404).
        """
        team_ids = await self.team_service.get_team_ids_for_user(user_id)
        if team_id is not None:
            if team_id not in team_ids:
                raise NotFoundError(detail=f"Team '{team_id}' not found")
            team_ids = [team_id]
        base_query = select(View).where(View.team_id.in_(team_ids))
        opts = QueryOptions(base_query=base_query)
        return await self.repo.get_all_paginated(pagination_params, entity_filter, opts)

    async def get_by_id(  # type: ignore[override]
        self, entity_id: uuid.UUID, *, user_id: uuid.UUID
    ) -> View:
        """Get a saved view by ID, enforcing team membership."""
        team_ids = await self.team_service.get_team_ids_for_user(user_id)
        view = await self.repo.get(entity_id, raise_error=True)
        if view.team_id not in team_ids:
            raise NotFoundError(detail=f"View '{entity_id}' not found")
        return view

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def create(  # type: ignore[override]
        self, entity: BaseModel, *, user_id: uuid.UUID
    ) -> View:
        """Create a saved view (member or admin), recording the owner.

        ``owner_id`` is injected from the authenticated user (not trusted from
        the client). ``filters`` defaults to an empty object when omitted so the
        JSONB column is never NULL.
        """
        team_id = getattr(entity, "team_id", None)
        if team_id is None:
            raise NotFoundError(detail="team_id is required")
        await self.team_service.require_team_access(
            user_id, team_id, min_role=TeamRole.member
        )
        return await self.repo.create(entity, owner_id=user_id)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    async def update(  # type: ignore[override]
        self, entity_id: uuid.UUID, entity: BaseModel, *, user_id: uuid.UUID
    ) -> View:
        """Update a saved view (member or admin of the view's team).

        Used only by an explicit re-save — dirty local changes never reach this
        path (VAL-VIEWS-006).
        """
        view = await self.get_by_id(entity_id, user_id=user_id)
        await self.team_service.require_team_access(
            user_id, view.team_id, min_role=TeamRole.member
        )
        return await self.repo.update(entity_id, entity)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def delete(  # type: ignore[override]
        self, entity_id: uuid.UUID, *, user_id: uuid.UUID
    ) -> None:
        """Delete a saved view (member or admin)."""
        view = await self.get_by_id(entity_id, user_id=user_id)
        await self.team_service.require_team_access(
            user_id, view.team_id, min_role=TeamRole.member
        )
        await self.repo.delete(entity_id)
