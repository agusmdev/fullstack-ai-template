"""Activity service — read-only listing + internal write (auto-generated).

Activity entries are **auto-generated** by ``IssueService`` on issue mutations
(status/assignee/priority/title/label changes) and exposed **read-only** to
clients (VAL-ACTIVITY-009). This service therefore exposes:

  - ``get_all_paginated`` / ``get_by_id`` — team-scoped **reads** (any team
    member/guest can view the activity of their team's issues).
  - ``record`` — the **internal write** used by ``IssueService`` to append an
    entry. It performs no authorization (the calling service has already
    authorized the underlying issue mutation); it only persists the entry.

Reads enforce team scoping transitively via the entry's issue's team, mirroring
the CommentService pattern: a foreign-team issue's activity is never leaked
(404, consistent with cross-team denial).
"""

import uuid
from typing import Any

from fastapi_filter.base.filter import BaseFilterModel
from fastapi_pagination import Page, Params
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.modules.activity.models import Activity
from app.modules.activity.repository import ActivityRepository
from app.modules.issues.models import Issue
from app.modules.issues.repository import IssueRepository
from app.modules.teams.service import TeamService
from app.repositories.base_repository import QueryOptions
from app.repositories.exceptions import NotFoundError
from app.services.base_crud_service import BaseService


class ActivityService(BaseService[Activity]):
    """Service for Activity entity (team-scoped reads + internal writes)."""

    repo: ActivityRepository
    team_service: TeamService
    issue_repo: IssueRepository

    def __init__(
        self,
        repo: ActivityRepository,
        team_service: TeamService,
        issue_repo: IssueRepository,
    ) -> None:
        self.repo = repo
        self.team_service = team_service
        self.issue_repo = issue_repo

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _resolve_issue_team(self, issue_id: uuid.UUID) -> tuple[Issue, uuid.UUID]:
        """Load an issue and return (issue, team_id).

        Raises :class:`NotFoundError` (404) if the issue is missing — a foreign
        issue's existence is never leaked (consistent with cross-team denial).
        """
        issue = await self.issue_repo.get(issue_id, raise_error=False)
        if issue is None:
            raise NotFoundError(detail=f"Issue '{issue_id}' not found")
        return issue, issue.team_id

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
    ) -> Page[Activity]:
        """List activity for the user's teams, newest-first by default.

        Scope: an activity entry is visible if its issue belongs to one of the
        user's teams. Optional ``issue_id`` restricts to activity on that issue
        (used by the issue drawer feed); the issue's team membership is confirmed
        first so a foreign issue's activity is never leaked. Optional ``team_id``
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
        base_query = (
            select(Activity)
            .options(selectinload(Activity.actor))
            .where(Activity.issue_id.in_(team_issue_ids))
        )
        if issue_id is not None:
            base_query = base_query.where(Activity.issue_id == issue_id)
        opts = QueryOptions(base_query=base_query)
        return await self.repo.get_all_paginated(pagination_params, entity_filter, opts)

    async def get_by_id(  # type: ignore[override]
        self, entity_id: uuid.UUID, *, user_id: uuid.UUID
    ) -> Activity:
        """Get an activity by ID, enforcing the issue's team membership."""
        team_ids = await self.team_service.get_team_ids_for_user(user_id)
        activity = await self.repo.get(entity_id, raise_error=True)
        issue = await self.issue_repo.get(activity.issue_id, raise_error=False)
        if issue is None or issue.team_id not in team_ids:
            raise NotFoundError(detail=f"Activity '{entity_id}' not found")
        return activity

    # ------------------------------------------------------------------
    # Write (internal — called by IssueService after it authorizes the
    # underlying issue mutation; no client-facing create endpoint exists).
    # ------------------------------------------------------------------

    async def record(
        self,
        *,
        issue_id: uuid.UUID,
        actor_id: uuid.UUID,
        activity_type: str,
        payload: dict[str, Any],
    ) -> Activity:
        """Append an auto-generated activity entry (no authorization).

        Called by ``IssueService`` for each qualifying issue mutation
        (status/assignee/priority/title/label change). The caller has already
        authorized the issue mutation, so this performs no team-access check; it
        only persists the entry. Returns the persisted entry (actor not
        eager-loaded here — callers do not read the return value; the feed
        re-fetches via ``get_all_paginated``).
        """
        return await self.repo.create(
            {
                "issue_id": issue_id,
                "actor_id": actor_id,
                "type": activity_type,
                "payload": payload,
            }
        )
