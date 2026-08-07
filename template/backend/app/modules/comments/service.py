"""Comment service — business logic layer (team-scoped, author/admin ownership).

Enforces:
  - Team scoping: comments are visible only to members of the comment's issue's
    team (transitive via ``issue.team_id``).
  - Team membership: creating a comment requires the ``member`` role — guests
    are read-only (VAL-CROSS-025).
  - Non-empty body: a blank or whitespace-only body is rejected with 422
    (VAL-COMMENTS-002).
  - Author/admin ownership: editing or deleting a comment is restricted to the
    comment's author or a team admin (VAL-COMMENTS-005, VAL-COMMENTS-008).
  - No N+1: the author is eager-loaded via ``selectinload`` on list and detail.
"""

import uuid

from fastapi import HTTPException
from fastapi_filter.base.filter import BaseFilterModel
from fastapi_pagination import Page, Params
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.modules.comments.models import Comment
from app.modules.comments.repository import CommentRepository
from app.modules.issues.models import Issue
from app.modules.issues.repository import IssueRepository
from app.modules.teams.models import TeamRole
from app.modules.teams.service import TeamService
from app.repositories.base_repository import QueryOptions
from app.repositories.exceptions import ForbiddenError, NotFoundError
from app.services.base_crud_service import BaseService


class CommentService(BaseService[Comment]):
    """Service for Comment entity with team-membership scoping + ownership."""

    repo: CommentRepository
    team_service: TeamService
    issue_repo: IssueRepository

    def __init__(
        self,
        repo: CommentRepository,
        team_service: TeamService,
        issue_repo: IssueRepository,
    ) -> None:
        self.repo = repo
        self.team_service = team_service
        self.issue_repo = issue_repo

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_body(body: str) -> str:
        """Strip surrounding whitespace. Empty/whitespace-only → None (rejected)."""
        return body.strip()

    async def _resolve_issue_team(self, issue_id: uuid.UUID) -> tuple[Issue, uuid.UUID]:
        """Load an issue and return (issue, team_id).

        Raises :class:`NotFoundError` (404) if the issue is missing — a foreign
        issue's existence is never leaked (consistent with cross-team denial).
        """
        issue = await self.issue_repo.get(issue_id, raise_error=False)
        if issue is None:
            raise NotFoundError(detail=f"Issue '{issue_id}' not found")
        return issue, issue.team_id

    async def _assert_can_modify(
        self, comment: Comment, team_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        """Allow edit/delete only for the comment's author or a team admin.

        Raises :class:`ForbiddenError` (403) for any other member — the caller
        is a confirmed member (the comment is visible to them) but lacks
        ownership (VAL-COMMENTS-008). Team admins can modify any comment.
        """
        if comment.author_id == user_id:
            return
        role_map = await self.team_service.get_role_map_for_user(user_id)
        if role_map.get(team_id) == TeamRole.admin:
            return
        raise ForbiddenError(detail="You can only edit or delete your own comments")

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
    ) -> Page[Comment]:
        """List comments for the user's teams, newest-first by default.

        Scope: a comment is visible if its issue belongs to one of the user's
        teams. Optional ``issue_id`` restricts to comments on that issue (used
        by the issue drawer thread); the issue's team membership is confirmed
        first so a foreign issue's comments are never leaked. Optional
        ``team_id`` restricts to a single team (must be a member, else 404).
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
            select(Comment)
            .options(selectinload(Comment.author))
            .where(Comment.issue_id.in_(team_issue_ids))
        )
        if issue_id is not None:
            base_query = base_query.where(Comment.issue_id == issue_id)
        opts = QueryOptions(base_query=base_query)
        return await self.repo.get_all_paginated(pagination_params, entity_filter, opts)

    async def get_by_id(  # type: ignore[override]
        self, entity_id: uuid.UUID, *, user_id: uuid.UUID
    ) -> Comment:
        """Get a comment by ID, enforcing the issue's team membership."""
        team_ids = await self.team_service.get_team_ids_for_user(user_id)
        comment = await self.repo.get(entity_id, raise_error=True)
        issue = await self.issue_repo.get(comment.issue_id, raise_error=False)
        if issue is None or issue.team_id not in team_ids:
            raise NotFoundError(detail=f"Comment '{entity_id}' not found")
        return comment

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def create(  # type: ignore[override]
        self, entity: BaseModel, *, user_id: uuid.UUID
    ) -> Comment:
        """Create a comment (member or admin of the issue's team).

        - Validates the issue exists and belongs to one of the user's teams.
        - Requires the ``member`` role on that team (guests are read-only).
        - Rejects an empty/whitespace-only body with 422 (VAL-COMMENTS-002).
        - Sets ``author_id`` to the authenticated user.
        - Reloads to eager-load the author for the response.
        """
        issue_id = getattr(entity, "issue_id", None)
        body = getattr(entity, "body", None)
        if issue_id is None:
            raise NotFoundError(detail="issue_id is required")

        _issue, team_id = await self._resolve_issue_team(issue_id)
        await self.team_service.require_team_access(
            user_id, team_id, min_role=TeamRole.member
        )

        if body is None:
            raise HTTPException(status_code=422, detail="Comment body is required")
        normalized = self._normalize_body(body)
        if not normalized:
            raise HTTPException(status_code=422, detail="Comment body cannot be empty")

        created = await self.repo.create(entity, author_id=user_id)
        # Reload to eager-load the author — INSERT RETURNING does not populate
        # relationships, and the response serializes the nested AuthorBrief.
        return await self.repo.get(created.id, raise_error=True)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    async def update(  # type: ignore[override]
        self, entity_id: uuid.UUID, entity: BaseModel, *, user_id: uuid.UUID
    ) -> Comment:
        """Edit a comment's body — author or team admin only.

        Updates the body in place (no duplicate/comment added, no reload)
        (VAL-COMMENTS-005). Rejects an empty/whitespace-only body with 422.
        """
        comment = await self.get_by_id(entity_id, user_id=user_id)
        issue = await self.issue_repo.get(comment.issue_id, raise_error=False)
        team_id = issue.team_id if issue is not None else None
        if team_id is None:
            raise NotFoundError(detail=f"Comment '{entity_id}' not found")
        await self._assert_can_modify(comment, team_id, user_id)

        body = getattr(entity, "body", None)
        if body is None:
            raise HTTPException(status_code=422, detail="Comment body is required")
        normalized = self._normalize_body(body)
        if not normalized:
            raise HTTPException(status_code=422, detail="Comment body cannot be empty")

        return await self.repo.update(entity_id, entity)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def delete(  # type: ignore[override]
        self, entity_id: uuid.UUID, *, user_id: uuid.UUID
    ) -> None:
        """Delete a comment — author or team admin only (VAL-COMMENTS-006).

        Removes the comment from the thread; other comments remain.
        """
        comment = await self.get_by_id(entity_id, user_id=user_id)
        issue = await self.issue_repo.get(comment.issue_id, raise_error=False)
        team_id = issue.team_id if issue is not None else None
        if team_id is None:
            raise NotFoundError(detail=f"Comment '{entity_id}' not found")
        await self._assert_can_modify(comment, team_id, user_id)
        await self.repo.delete(entity_id)
