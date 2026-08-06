"""Label service — business logic layer (team-scoped).

Enforces that a user can only read/write labels for teams they belong to.
Creating/updating/deleting labels requires the ``member`` role (admins and
members manage labels; guests are read-only).
"""

import uuid

from fastapi_filter.base.filter import BaseFilterModel
from fastapi_pagination import Page, Params
from pydantic import BaseModel
from sqlalchemy import select

from app.modules.labels.models import Label
from app.modules.labels.repository import LabelRepository
from app.modules.teams.models import TeamRole
from app.modules.teams.service import TeamService
from app.repositories.base_repository import QueryOptions
from app.repositories.exceptions import NotFoundError
from app.services.base_crud_service import BaseService


class LabelService(BaseService[Label]):
    """Service for Label entity with team-membership-based scoping."""

    repo: LabelRepository
    team_service: TeamService

    def __init__(self, repo: LabelRepository, team_service: TeamService) -> None:
        self.repo = repo
        self.team_service = team_service

    async def get_all_paginated(  # type: ignore[override]
        self,
        pagination_params: Params,
        entity_filter: BaseFilterModel | None = None,
        *,
        user_id: uuid.UUID,
        team_id: uuid.UUID | None = None,
    ) -> Page[Label]:
        """List labels for the user's teams.

        If ``team_id`` is provided, the result is restricted to that team
        (the user must be a member, else 404).
        """
        team_ids = await self.team_service.get_team_ids_for_user(user_id)
        if team_id is not None:
            if team_id not in team_ids:
                raise NotFoundError(detail=f"Team '{team_id}' not found")
            team_ids = [team_id]
        base_query = select(Label).where(Label.team_id.in_(team_ids))
        opts = QueryOptions(base_query=base_query)
        return await self.repo.get_all_paginated(pagination_params, entity_filter, opts)

    async def get_by_id(  # type: ignore[override]
        self, entity_id: uuid.UUID, *, user_id: uuid.UUID
    ) -> Label:
        """Get a label by ID, enforcing team membership."""
        team_ids = await self.team_service.get_team_ids_for_user(user_id)
        label = await self.repo.get(entity_id, raise_error=True)
        if label.team_id not in team_ids:
            raise NotFoundError(detail=f"Label '{entity_id}' not found")
        return label

    async def create(  # type: ignore[override]
        self, entity: BaseModel, *, user_id: uuid.UUID
    ) -> Label:
        """Create a label (member or admin)."""
        team_id = getattr(entity, "team_id", None)
        if team_id is None:
            raise NotFoundError(detail="team_id is required")
        await self.team_service.require_team_access(
            user_id, team_id, min_role=TeamRole.member
        )
        return await self.repo.create(entity)

    async def update(  # type: ignore[override]
        self, entity_id: uuid.UUID, entity: BaseModel, *, user_id: uuid.UUID
    ) -> Label:
        """Update a label (member or admin)."""
        label = await self.get_by_id(entity_id, user_id=user_id)
        await self.team_service.require_team_access(
            user_id, label.team_id, min_role=TeamRole.member
        )
        return await self.repo.update(entity_id, entity)

    async def delete(  # type: ignore[override]
        self, entity_id: uuid.UUID, *, user_id: uuid.UUID
    ) -> None:
        """Delete a label (member or admin)."""
        label = await self.get_by_id(entity_id, user_id=user_id)
        await self.team_service.require_team_access(
            user_id, label.team_id, min_role=TeamRole.member
        )
        await self.repo.delete(entity_id)
