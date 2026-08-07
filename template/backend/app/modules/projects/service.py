"""Project service — business logic layer (team-scoped).

Enforces that a user can only read/write projects for teams they belong to.
Creating/updating/deleting projects requires the ``member`` role. When a lead is
set, it is validated to be a member of the project's team (defense-in-depth).
"""

import uuid

from fastapi_filter.base.filter import BaseFilterModel
from fastapi_pagination import Page, Params
from pydantic import BaseModel
from sqlalchemy import select

from app.modules.projects.models import Project
from app.modules.projects.repository import ProjectRepository
from app.modules.teams.models import TeamRole
from app.modules.teams.service import TeamService
from app.repositories.base_repository import QueryOptions
from app.repositories.exceptions import NotFoundError
from app.services.base_crud_service import BaseService


class ProjectService(BaseService[Project]):
    """Service for Project entity with team-membership-based scoping."""

    repo: ProjectRepository
    team_service: TeamService

    def __init__(self, repo: ProjectRepository, team_service: TeamService) -> None:
        self.repo = repo
        self.team_service = team_service

    # ------------------------------------------------------------------
    # Cross-team field validation (defense-in-depth)
    # ------------------------------------------------------------------
    # A member could attach a foreign-team lead by guessing a user UUID. This
    # helper verifies the lead is a member of the project's team, raising
    # NotFoundError (404, never 403) so a foreign identity is never leaked —
    # consistent with the cross-team denial convention used by IssueService.

    async def _validate_lead_in_team(
        self, lead_id: uuid.UUID, team_id: uuid.UUID
    ) -> None:
        """Verify the lead is a member of ``team_id``."""
        membership = await self.team_service.get_membership(lead_id, team_id)
        if membership is None:
            raise NotFoundError(detail=f"Lead '{lead_id}' is not a member of this team")

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
    ) -> Page[Project]:
        """List projects for the user's teams.

        If ``team_id`` is provided, the result is restricted to that team
        (the user must be a member, else 404).
        """
        team_ids = await self.team_service.get_team_ids_for_user(user_id)
        if team_id is not None:
            if team_id not in team_ids:
                raise NotFoundError(detail=f"Team '{team_id}' not found")
            team_ids = [team_id]
        base_query = select(Project).where(Project.team_id.in_(team_ids))
        opts = QueryOptions(base_query=base_query)
        return await self.repo.get_all_paginated(pagination_params, entity_filter, opts)

    async def get_by_id(  # type: ignore[override]
        self, entity_id: uuid.UUID, *, user_id: uuid.UUID
    ) -> Project:
        """Get a project by ID, enforcing team membership."""
        team_ids = await self.team_service.get_team_ids_for_user(user_id)
        project = await self.repo.get(entity_id, raise_error=True)
        if project.team_id not in team_ids:
            raise NotFoundError(detail=f"Project '{entity_id}' not found")
        return project

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def create(  # type: ignore[override]
        self, entity: BaseModel, *, user_id: uuid.UUID
    ) -> Project:
        """Create a project (member or admin).

        Defaults ``status`` to ``planned`` (non-terminal). When a lead is
        provided, validates they are a member of the project's team.
        """
        team_id = getattr(entity, "team_id", None)
        if team_id is None:
            raise NotFoundError(detail="team_id is required")
        await self.team_service.require_team_access(
            user_id, team_id, min_role=TeamRole.member
        )

        # Defense-in-depth: the lead must be a team member.
        lead_id = getattr(entity, "lead_id", None)
        if lead_id is not None:
            await self._validate_lead_in_team(lead_id, team_id)

        return await self.repo.create(entity)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    async def update(  # type: ignore[override]
        self, entity_id: uuid.UUID, entity: BaseModel, *, user_id: uuid.UUID
    ) -> Project:
        """Update a project (member or admin of the project's team).

        When a new lead is provided, validates they are a member of the
        project's team.
        """
        project = await self.get_by_id(entity_id, user_id=user_id)
        await self.team_service.require_team_access(
            user_id, project.team_id, min_role=TeamRole.member
        )

        # Defense-in-depth: validate a new lead against the project's team.
        lead_id = getattr(entity, "lead_id", None)
        if lead_id is not None:
            await self._validate_lead_in_team(lead_id, project.team_id)

        return await self.repo.update(entity_id, entity)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def delete(  # type: ignore[override]
        self, entity_id: uuid.UUID, *, user_id: uuid.UUID
    ) -> None:
        """Delete a project (member or admin). Issues are detached (SET NULL)."""
        project = await self.get_by_id(entity_id, user_id=user_id)
        await self.team_service.require_team_access(
            user_id, project.team_id, min_role=TeamRole.member
        )
        await self.repo.delete(entity_id)
