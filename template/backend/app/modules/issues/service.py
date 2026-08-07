"""Issue service — business logic layer (team-scoped, ownership-enforced).

Enforces:
  - Team scoping: every query is restricted to the user's team memberships.
  - Team membership: writes require at least ``member`` role — including the
    labels sub-resource (``add_label``/``remove_label``); guests are read-only
    (VAL-CROSS-025).
  - Cross-team field validation (defense-in-depth): referenced entities
    (label/status/assignee) are verified to belong to the issue's team.
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

from app.modules.cycles.repository import CycleRepository
from app.modules.issues.models import Issue
from app.modules.issues.repository import IssueRepository
from app.modules.labels.models import issue_label
from app.modules.labels.repository import LabelRepository
from app.modules.projects.repository import ProjectRepository
from app.modules.teams.models import TeamRole
from app.modules.teams.service import TeamService
from app.modules.workflows.models import WorkflowState
from app.modules.workflows.repository import WorkflowStateRepository
from app.repositories.base_repository import QueryOptions
from app.repositories.exceptions import NotFoundError, ReferencedError
from app.services.base_crud_service import BaseService


class IssueService(BaseService[Issue]):
    """Service for Issue entity with team-membership-based scoping."""

    repo: IssueRepository
    team_service: TeamService
    workflow_state_repo: WorkflowStateRepository
    label_repo: LabelRepository
    project_repo: ProjectRepository
    cycle_repo: CycleRepository

    def __init__(
        self,
        repo: IssueRepository,
        team_service: TeamService,
        workflow_state_repo: WorkflowStateRepository,
        label_repo: LabelRepository,
        project_repo: ProjectRepository,
        cycle_repo: CycleRepository,
    ) -> None:
        self.repo = repo
        self.team_service = team_service
        self.workflow_state_repo = workflow_state_repo
        self.label_repo = label_repo
        self.project_repo = project_repo
        self.cycle_repo = cycle_repo

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
    # Cross-team field validation (defense-in-depth)
    # ------------------------------------------------------------------
    # A member could attach a foreign-team referenced entity (label/status/
    # assignee) by guessing its UUID. These helpers verify each referenced
    # entity belongs to the same team as the issue being mutated. A 404
    # (NotFound) is raised rather than 403 so a foreign-team entity's existence
    # is never leaked (consistent with cross-team denial).

    async def _validate_label_in_team(
        self, label_id: uuid.UUID, team_id: uuid.UUID
    ) -> None:
        """Verify a label exists and belongs to ``team_id``."""
        label = await self.label_repo.get(label_id, raise_error=False)
        if label is None or label.team_id != team_id:
            raise NotFoundError(detail=f"Label '{label_id}' not found")

    async def _validate_status_in_team(
        self, status_id: uuid.UUID, team_id: uuid.UUID
    ) -> None:
        """Verify a workflow status exists and belongs to ``team_id``."""
        state = await self.workflow_state_repo.get(status_id, raise_error=False)
        if state is None or state.team_id != team_id:
            raise NotFoundError(detail=f"Status '{status_id}' not found")

    async def _validate_assignee_in_team(
        self, assignee_id: uuid.UUID, team_id: uuid.UUID
    ) -> None:
        """Verify the assignee is a member of ``team_id``."""
        membership = await self.team_service.get_membership(assignee_id, team_id)
        if membership is None:
            raise NotFoundError(
                detail=f"Assignee '{assignee_id}' is not a member of this team"
            )

    async def _validate_project_in_team(
        self, project_id: uuid.UUID, team_id: uuid.UUID
    ) -> None:
        """Verify a project exists and belongs to ``team_id``."""
        project = await self.project_repo.get(project_id, raise_error=False)
        if project is None or project.team_id != team_id:
            raise NotFoundError(detail=f"Project '{project_id}' not found")

    async def _validate_cycle_in_team(
        self, cycle_id: uuid.UUID, team_id: uuid.UUID
    ) -> None:
        """Verify a cycle exists and belongs to ``team_id``."""
        cycle = await self.cycle_repo.get(cycle_id, raise_error=False)
        if cycle is None or cycle.team_id != team_id:
            raise NotFoundError(detail=f"Cycle '{cycle_id}' not found")

    async def _validate_parent_in_team(
        self, parent_id: uuid.UUID, team_id: uuid.UUID
    ) -> Issue:
        """Verify the parent issue exists and belongs to ``team_id``.

        Returns the parent issue so callers can traverse its ancestry for cycle
        detection. A 404 (NotFound) is raised rather than 403 so a foreign-team
        issue's existence is never leaked (consistent with cross-team denial).
        """
        parent = await self.repo.get(parent_id, raise_error=False)
        if parent is None or parent.team_id != team_id:
            raise NotFoundError(detail=f"Parent issue '{parent_id}' not found")
        return parent

    async def _check_no_cycle(
        self, issue_id: uuid.UUID, proposed_parent_id: uuid.UUID, team_id: uuid.UUID
    ) -> None:
        """Reject a parent assignment that would create a circular reference.

        Walks up the parent chain from ``proposed_parent_id``. If ``issue_id``
        is found among the ancestors, the assignment would create a cycle and a
        :class:`ReferencedError` (400) is raised. The walk is bounded to a
        reasonable depth as a safety net against pathological chains.
        """
        current = proposed_parent_id
        depth = 0
        max_depth = 100
        while current is not None and depth < max_depth:
            if current == issue_id:
                raise ReferencedError(
                    detail="Setting this parent would create a circular reference"
                )
            ancestor = await self.repo.get(current, raise_error=False)
            if ancestor is None or ancestor.team_id != team_id:
                break
            current = ancestor.parent_id
            depth += 1

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
        unassigned: bool | None = None,
        parent_id: uuid.UUID | None = None,
        top_level: bool | None = None,
    ) -> Page[Issue]:
        """List issues for the user's teams, eager-loading labels (no N+1).

        Supports optional ``team_id`` (restrict to one team), ``label_id``
        (filter by M2M label membership via subquery), ``unassigned`` (filter
        to issues with no assignee — VAL-ISSUES-021), ``parent_id`` (fetch the
        children of a specific parent issue — VAL-SUBISSUES-001), and
        ``top_level`` (filter to issues with no parent — parent_id IS NULL).
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
        if unassigned:
            base_query = base_query.where(Issue.assignee_id.is_(None))
        if parent_id is not None:
            base_query = base_query.where(Issue.parent_id == parent_id)
        if top_level:
            base_query = base_query.where(Issue.parent_id.is_(None))
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

        # Resolve default status to team's first workflow state, or validate a
        # caller-supplied status belongs to the issue's team (defense-in-depth).
        status_id = getattr(entity, "status_id", None)
        if status_id is None:
            status_id = await self._resolve_default_status(team_id)
        else:
            await self._validate_status_in_team(status_id, team_id)

        # Defense-in-depth: referenced entities must belong to the issue's team.
        assignee_id = getattr(entity, "assignee_id", None)
        if assignee_id is not None:
            await self._validate_assignee_in_team(assignee_id, team_id)

        cycle_id = getattr(entity, "cycle_id", None)
        if cycle_id is not None:
            await self._validate_cycle_in_team(cycle_id, team_id)

        label_ids = getattr(entity, "label_ids", None)
        if label_ids:
            for lid in label_ids:
                await self._validate_label_in_team(lid, team_id)

        # Validate the parent issue (sub-issues) belongs to the same team
        # (defense-in-depth — VAL-SUBISSUES-001).
        parent_id = getattr(entity, "parent_id", None)
        if parent_id is not None:
            await self._validate_parent_in_team(parent_id, team_id)

        # Allocate identifier (atomic; held until create commits).
        identifier = await self.repo.allocate_identifier(team_id)

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

        # Defense-in-depth: validate referenced entities against the issue's
        # team so a member can't attach a foreign-team status/assignee/project
        # by UUID. ``project_id`` may be None to clear the assignment (no
        # validation needed in that case).
        status_id = getattr(entity, "status_id", None)
        if status_id is not None:
            await self._validate_status_in_team(status_id, issue.team_id)
        assignee_id = getattr(entity, "assignee_id", None)
        if assignee_id is not None:
            await self._validate_assignee_in_team(assignee_id, issue.team_id)
        project_id = getattr(entity, "project_id", None)
        if project_id is not None:
            await self._validate_project_in_team(project_id, issue.team_id)
        cycle_id = getattr(entity, "cycle_id", None)
        if cycle_id is not None:
            await self._validate_cycle_in_team(cycle_id, issue.team_id)

        # Validate parent_id (sub-issues): must belong to the same team, cannot
        # be the issue itself, and must not create a circular reference
        # (VAL-SUBISSUES-001, VAL-SUBISSUES-005). A None parent_id (clear) is
        # always valid — it detaches the child to top-level.
        parent_id = getattr(entity, "parent_id", None)
        if parent_id is not None:
            if parent_id == entity_id:
                raise ReferencedError(detail="An issue cannot be its own parent")
            await self._validate_parent_in_team(parent_id, issue.team_id)
            await self._check_no_cycle(entity_id, parent_id, issue.team_id)

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
        """Add a label to an issue (idempotent). Both must be same-team.

        Enforces the ``member`` role — guests are read-only (VAL-CROSS-025) —
        and validates the label belongs to the issue's team (defense-in-depth).
        """
        issue = await self.get_by_id(entity_id, user_id=user_id)
        await self.team_service.require_team_access(
            user_id, issue.team_id, min_role=TeamRole.member
        )
        await self._validate_label_in_team(label_id, issue.team_id)
        await self.repo.add_label(issue.id, label_id)
        return await self.repo.get(issue.id, raise_error=True)

    async def remove_label(  # type: ignore[override]
        self,
        entity_id: uuid.UUID,
        label_id: uuid.UUID,
        *,
        user_id: uuid.UUID,
    ) -> Issue:
        """Remove a label from an issue.

        Enforces the ``member`` role — guests are read-only (VAL-CROSS-025),
        mirroring ``update()``/``delete()``.
        """
        issue = await self.get_by_id(entity_id, user_id=user_id)
        await self.team_service.require_team_access(
            user_id, issue.team_id, min_role=TeamRole.member
        )
        await self.repo.remove_label(issue.id, label_id)
        return await self.repo.get(issue.id, raise_error=True)
