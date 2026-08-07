"""IssueDependency service — business logic layer (team-scoped, cycle guard).

Enforces:
  - Same-team: both endpoints of a dependency must belong to the same team
    (VAL-DEPS-005). A cross-team reference raises ``NotFoundError`` (404) so a
    foreign issue's existence is never leaked (consistent with cross-team denial
    elsewhere).
  - Team membership: writes require the ``member`` role (VAL-CROSS-025).
  - No self-dependency: an issue cannot block itself (422).
  - No circular dependency: adding an edge that would close a cycle is rejected
    with 409 (VAL-DEPS-003).
  - Read scoping: list/get only surface dependencies whose endpoints belong to
    the user's teams.
"""

import uuid
from collections import defaultdict

from fastapi import HTTPException
from fastapi_filter.base.filter import BaseFilterModel
from fastapi_pagination import Page, Params
from pydantic import BaseModel
from sqlalchemy import or_, select

from app.modules.issue_dependencies.models import IssueDependency
from app.modules.issue_dependencies.repository import IssueDependencyRepository
from app.modules.issues.models import Issue
from app.modules.issues.repository import IssueRepository
from app.modules.teams.models import TeamRole
from app.modules.teams.service import TeamService
from app.repositories.base_repository import QueryOptions
from app.repositories.exceptions import NotFoundError
from app.services.base_crud_service import BaseService


class IssueDependencyService(BaseService[IssueDependency]):
    """Service for IssueDependency entity with team-membership scoping."""

    repo: IssueDependencyRepository
    team_service: TeamService
    issue_repo: IssueRepository

    def __init__(
        self,
        repo: IssueDependencyRepository,
        team_service: TeamService,
        issue_repo: IssueRepository,
    ) -> None:
        self.repo = repo
        self.team_service = team_service
        self.issue_repo = issue_repo

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _resolve_pair_team(
        self, blocker_id: uuid.UUID, blocked_id: uuid.UUID
    ) -> uuid.UUID:
        """Load both endpoints and return their common team id.

        Raises :class:`NotFoundError` (404) if either issue is missing or the two
        issues belong to different teams (VAL-DEPS-005) — a foreign issue's
        existence is never leaked.
        """
        blocker = await self.issue_repo.get(blocker_id, raise_error=False)
        blocked = await self.issue_repo.get(blocked_id, raise_error=False)
        if blocker is None or blocked is None:
            raise NotFoundError(detail="Referenced issue not found")
        if blocker.team_id != blocked.team_id:
            raise NotFoundError(detail="Both issues must belong to the same team")
        return blocker.team_id

    async def _check_no_cycle(
        self, blocker_id: uuid.UUID, blocked_id: uuid.UUID, team_id: uuid.UUID
    ) -> None:
        """Reject an edge (blocker_id → blocked_id) that would create a cycle.

        Builds the team's existing dependency graph (blocker → blocked) and
        traverses from ``blocked_id`` following those edges. If ``blocker_id`` is
        reachable, the new edge would close a loop and a 409 is raised
        (VAL-DEPS-003). The traversal is bounded by the number of existing edges
        (visited set) so it always terminates.
        """
        edges = await self.repo.get_edges_for_team(team_id)
        adjacency: dict[uuid.UUID, list[uuid.UUID]] = defaultdict(list)
        for src, dst in edges:
            adjacency[src].append(dst)

        seen: set[uuid.UUID] = set()
        stack = [blocked_id]
        while stack:
            node = stack.pop()
            if node == blocker_id:
                raise HTTPException(
                    status_code=409,
                    detail="Creating this dependency would form a circular dependency",
                )
            if node in seen:
                continue
            seen.add(node)
            stack.extend(adjacency.get(node, []))

    # ------------------------------------------------------------------
    # Read (team-scoped)
    # ------------------------------------------------------------------

    async def get_all_paginated(  # type: ignore[override]
        self,
        pagination_params: Params,
        entity_filter: BaseFilterModel | None = None,
        *,
        user_id: uuid.UUID,
        issue_id: uuid.UUID | None = None,
        team_id: uuid.UUID | None = None,
    ) -> Page[IssueDependency]:
        """List dependencies for the user's teams.

        Scope: a dependency is visible if **both** endpoints belong to one of the
        user's teams. Optional ``issue_id`` restricts to dependencies involving
        that issue (either side — reciprocal, VAL-DEPS-002). Optional ``team_id``
        restricts to a single team (must be a member, else 404).
        """
        team_ids = await self.team_service.get_team_ids_for_user(user_id)
        if team_id is not None:
            if team_id not in team_ids:
                raise NotFoundError(detail=f"Team '{team_id}' not found")
            team_ids = [team_id]

        # When filtering by a specific issue, confirm the caller can see that
        # issue's team (no cross-team leak).
        if issue_id is not None:
            issue = await self.issue_repo.get(issue_id, raise_error=False)
            if issue is None or issue.team_id not in team_ids:
                raise NotFoundError(detail=f"Issue '{issue_id}' not found")

        team_issue_ids = select(Issue.id).where(Issue.team_id.in_(team_ids))
        base_query = select(IssueDependency).where(
            IssueDependency.blocker_id.in_(team_issue_ids),
            IssueDependency.blocked_id.in_(team_issue_ids),
        )
        if issue_id is not None:
            base_query = base_query.where(
                or_(
                    IssueDependency.blocker_id == issue_id,
                    IssueDependency.blocked_id == issue_id,
                )
            )
        opts = QueryOptions(base_query=base_query)
        return await self.repo.get_all_paginated(pagination_params, entity_filter, opts)

    async def get_by_id(  # type: ignore[override]
        self, entity_id: uuid.UUID, *, user_id: uuid.UUID
    ) -> IssueDependency:
        """Get a dependency by ID, enforcing team membership on both endpoints."""
        team_ids = await self.team_service.get_team_ids_for_user(user_id)
        dep = await self.repo.get(entity_id, raise_error=True)
        blocker = await self.issue_repo.get(dep.blocker_id, raise_error=False)
        blocked = await self.issue_repo.get(dep.blocked_id, raise_error=False)
        if (
            blocker is None
            or blocked is None
            or blocker.team_id not in team_ids
            or blocked.team_id not in team_ids
        ):
            raise NotFoundError(detail=f"Dependency '{entity_id}' not found")
        return dep

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def create(  # type: ignore[override]
        self, entity: BaseModel, *, user_id: uuid.UUID
    ) -> IssueDependency:
        """Create a 'blocks' dependency (member or admin of the issues' team).

        - Rejects self-dependency (an issue blocking itself) with 422.
        - Validates both endpoints exist and belong to the same team (VAL-DEPS-005).
        - Requires ``member`` role on that team (VAL-CROSS-025).
        - Rejects cycle-forming edges with 409 (VAL-DEPS-003).
        """
        blocker_id = getattr(entity, "blocker_id", None)
        blocked_id = getattr(entity, "blocked_id", None)

        if blocker_id is None or blocked_id is None:
            raise NotFoundError(detail="blocker_id and blocked_id are required")
        if blocker_id == blocked_id:
            raise HTTPException(
                status_code=422,
                detail="An issue cannot depend on itself",
            )

        team_id = await self._resolve_pair_team(blocker_id, blocked_id)
        await self.team_service.require_team_access(
            user_id, team_id, min_role=TeamRole.member
        )
        await self._check_no_cycle(blocker_id, blocked_id, team_id)

        created = await self.repo.create(entity)
        # Reload to eager-load the blocker/blocked briefs — the INSERT RETURNING
        # path does not populate relationships, and the response serializes
        # nested briefs (VAL-DEPS-002 reciprocal display).
        return await self.repo.get(created.id, raise_error=True)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def delete(  # type: ignore[override]
        self, entity_id: uuid.UUID, *, user_id: uuid.UUID
    ) -> None:
        """Delete a dependency (member or admin). Removing it detaches the
        relationship from both issues (VAL-DEPS-004)."""
        dep = await self.get_by_id(entity_id, user_id=user_id)
        # Resolve the team from either endpoint (both same-team) and gate writes.
        blocker = await self.issue_repo.get(dep.blocker_id, raise_error=False)
        team_id = blocker.team_id if blocker is not None else None
        if team_id is None:
            raise NotFoundError(detail=f"Dependency '{entity_id}' not found")
        await self.team_service.require_team_access(
            user_id, team_id, min_role=TeamRole.member
        )
        await self.repo.delete(entity_id)
