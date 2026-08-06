"""Issue service — business logic layer (team-scoped, ownership-enforced).

Enforces:
  - Team scoping: every query is restricted to the user's team memberships.
  - Team membership: writes require at least ``member`` role.
  - Auto-identifier: ``TEAM-NN`` generated atomically on create.
  - Default status: falls back to the team's first workflow state (by position).
  - No N+1: labels eager-loaded via ``selectinload`` on list and detail queries.
"""

import uuid

from fastapi_filter.base.filter import BaseFilterModel
from fastapi_pagination import Page, Params
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.modules.issues.models import Issue
from app.modules.issues.repository import IssueRepository
from app.modules.labels.models import issue_label
from app.modules.teams.models import TeamRole
from app.modules.teams.service import TeamService
from app.modules.workflows.models import WorkflowState
from app.modules.workflows.repository import WorkflowStateRepository
from app.repositories.base_repository import QueryOptions
from app.repositories.exceptions import NotFoundError
from app.services.base_crud_service import BaseService


class IssueService(BaseService[Issue]):
    """Service for Issue entity with team-membership-based scoping."""

    repo: IssueRepository
    team_service: TeamService
    workflow_state_repo: WorkflowStateRepository

    def __init__(
        self,
        repo: IssueRepository,
        team_service: TeamService,
        workflow_state_repo: WorkflowStateRepository,
    ) -> None:
        self.repo = repo
        self.team_service = team_service
        self.workflow_state_repo = workflow_state_repo

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _resolve_default_status(self, team_id: uuid.UUID) -> uuid.UUID:
        """Return the ID of the team's first workflow state (by position)."""
        states = await self.workflow_state_repo.get_all(
            options=QueryOptions(
                base_query=select(WorkflowState)
                .where(WorkflowState.team_id == team_id)
                .order_by(WorkflowState.position)
            )
        )
        if not states:
            raise NotFoundError(
                detail=f"Team '{team_id}' has no workflow states configured"
            )
        return states[0].id

    async def _assert_team_member(
        self, issue: Issue, team_ids: list[uuid.UUID]
    ) -> None:
        """Raise NotFoundError if the issue belongs to a team outside team_ids."""
        if issue.team_id not in team_ids:
            raise NotFoundError(detail="Issue not found")

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
        label_id: uuid.UUID | None = None,
    ) -> Page[Issue]:
        """List issues for the user's teams, eager-loading labels (no N+1).

        Supports optional ``team_id`` (restrict to one team) and ``label_id``
        (filter by M2M label membership via subquery).
        """
        team_ids = await self.team_service.get_team_ids_for_user(user_id)
        if team_id is not None:
            if team_id not in team_ids:
                raise NotFoundError(detail=f"Team '{team_id}' not found")
            team_ids = [team_id]

        base_query = (
            select(Issue)
            .options(selectinload(Issue.labels))
            .where(Issue.team_id.in_(team_ids))
        )
        if label_id is not None:
            base_query = base_query.where(
                Issue.id.in_(
                    select(issue_label.c.issue_id).where(
                        issue_label.c.label_id == label_id
                    )
                )
            )
        opts = QueryOptions(base_query=base_query)
        return await self.repo.get_all_paginated(pagination_params, entity_filter, opts)

    async def get_by_id(  # type: ignore[override]
        self, entity_id: uuid.UUID, *, user_id: uuid.UUID
    ) -> Issue:
        """Get an issue by ID, enforcing team membership. Eager-loads labels."""
        team_ids = await self.team_service.get_team_ids_for_user(user_id)
        issue = await self.repo.get(entity_id, raise_error=True)
        await self._assert_team_member(issue, team_ids)
        return issue

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def create(  # type: ignore[override]
        self, entity: BaseModel, *, user_id: uuid.UUID
    ) -> Issue:
        """Create an issue, auto-generating the identifier and defaulting status.

        - Validates team membership (member or admin).
        - Defaults ``status_id`` to the team's first workflow state if omitted.
        - Allocates a monotonic, concurrency-safe ``TEAM-NN`` identifier.
        - Sets ``creator_id`` to the authenticated user.
        - Optionally attaches ``label_ids``.
        """
        team_id = getattr(entity, "team_id", None)
        if team_id is None:
            raise NotFoundError(detail="team_id is required")

        await self.team_service.require_team_access(
            user_id, team_id, min_role=TeamRole.member
        )

        # Resolve default status to team's first workflow state.
        status_id = getattr(entity, "status_id", None)
        if status_id is None:
            status_id = await self._resolve_default_status(team_id)

        # Allocate identifier (atomic; held until create commits).
        identifier = await self.repo.allocate_identifier(team_id)

        # Extract non-column fields before serialising for INSERT.
        label_ids = getattr(entity, "label_ids", None)

        # Exclude label_ids (not a model column) from the INSERT payload.
        create_data = entity.model_dump(exclude={"label_ids"})
        issue = await self.repo.create(
            create_data,
            identifier=identifier,
            creator_id=user_id,
            status_id=status_id,
        )

        # Attach labels if provided.
        if label_ids:
            await self.repo.attach_labels(issue.id, label_ids)
            # Reload to populate the labels relationship.
            issue = await self.repo.get(issue.id, raise_error=True)

        return issue

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    async def update(  # type: ignore[override]
        self, entity_id: uuid.UUID, entity: BaseModel, *, user_id: uuid.UUID
    ) -> Issue:
        """Update an issue (member or admin of the issue's team)."""
        issue = await self.get_by_id(entity_id, user_id=user_id)
        await self.team_service.require_team_access(
            user_id, issue.team_id, min_role=TeamRole.member
        )
        updated = await self.repo.update(entity_id, entity)
        # Reload to populate labels (update returns a fresh instance but
        # selectinload only fires on explicit select queries).
        return await self.repo.get(updated.id, raise_error=True)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def delete(  # type: ignore[override]
        self, entity_id: uuid.UUID, *, user_id: uuid.UUID
    ) -> None:
        """Delete an issue (member or admin of the issue's team)."""
        issue = await self.get_by_id(entity_id, user_id=user_id)
        await self.team_service.require_team_access(
            user_id, issue.team_id, min_role=TeamRole.member
        )
        await self.repo.delete(entity_id)

    # ------------------------------------------------------------------
    # Labels sub-resource
    # ------------------------------------------------------------------

    async def add_label(  # type: ignore[override]
        self,
        entity_id: uuid.UUID,
        label_id: uuid.UUID,
        *,
        user_id: uuid.UUID,
    ) -> Issue:
        """Add a label to an issue (idempotent). Both must be same-team."""
        issue = await self.get_by_id(entity_id, user_id=user_id)
        await self.repo.add_label(issue.id, label_id)
        return await self.repo.get(issue.id, raise_error=True)

    async def remove_label(  # type: ignore[override]
        self,
        entity_id: uuid.UUID,
        label_id: uuid.UUID,
        *,
        user_id: uuid.UUID,
    ) -> Issue:
        """Remove a label from an issue."""
        issue = await self.get_by_id(entity_id, user_id=user_id)
        await self.repo.remove_label(issue.id, label_id)
        return await self.repo.get(issue.id, raise_error=True)
