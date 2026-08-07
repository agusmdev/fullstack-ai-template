"""Tests for CommentService (team-scoped, author/admin ownership).

Covers:
  - Create persists a comment, sets author_id, rejects empty/whitespace body
    (VAL-COMMENTS-001, VAL-COMMENTS-002).
  - List scoped by issue_id returns the thread; cross-team issue → 404 (no leak).
  - Edit updates the body in place — author or team admin only (VAL-COMMENTS-005,
    VAL-COMMENTS-008).
  - Delete removes the comment — author or team admin only (VAL-COMMENTS-006).
  - Team membership enforced (member role required for create; guest blocked).
"""

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from fastapi_pagination import Params

from app.modules.comments.models import Comment
from app.modules.comments.schemas import CommentCreate, CommentUpdate
from app.modules.comments.service import CommentService
from app.modules.teams.models import TeamRole
from app.repositories.exceptions import ForbiddenError, NotFoundError

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

NOW = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def sample_user_id():
    return uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def other_user_id():
    return uuid.UUID("99999999-9999-9999-9999-999999999999")


@pytest.fixture
def sample_team_id():
    return uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
def other_team_id():
    return uuid.UUID("33333333-3333-3333-3333-333333333333")


@pytest.fixture
def issue_id():
    return uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


@pytest.fixture
def comment_id():
    return uuid.UUID("55555555-5555-5555-5555-555555555555")


@pytest.fixture
def issue_obj(issue_id, sample_team_id):
    return SimpleNamespace(id=issue_id, team_id=sample_team_id)


@pytest.fixture
def author_brief(sample_user_id):
    return SimpleNamespace(id=sample_user_id, display_name="Ada", email="ada@x.com")


@pytest.fixture
def comment_obj(comment_id, issue_id, sample_user_id, author_brief):
    return SimpleNamespace(
        id=comment_id,
        issue_id=issue_id,
        author_id=sample_user_id,
        body="Hello world",
        author=author_brief,
        created_at=NOW,
        updated_at=NOW,
    )


@pytest.fixture
def service(mock_comment_repository, mock_issue_repository, mock_team_service):
    return CommentService(
        repo=mock_comment_repository,
        team_service=mock_team_service,
        issue_repo=mock_issue_repository,
    )


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestCommentModel:
    def test_table_registered(self):
        from app.database.base import Base

        assert "comment" in Base.metadata.tables

    def test_model_fields(self):
        cols = {c.name for c in Comment.__table__.columns}
        assert {"id", "issue_id", "author_id", "body"} <= cols


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


class TestCreate:
    @pytest.mark.asyncio
    async def test_creates_comment_sets_author(
        self, service, mock_comment_repository, mock_issue_repository,
        mock_team_service, issue_obj, comment_obj,
        issue_id, sample_team_id, sample_user_id,
    ):
        """Add comment persists, author = authenticated user (VAL-COMMENTS-001)."""
        mock_issue_repository.get.return_value = issue_obj
        mock_comment_repository.create.return_value = comment_obj
        mock_comment_repository.get.return_value = comment_obj

        result = await service.create(
            CommentCreate(issue_id=issue_id, body="Hello world"),
            user_id=sample_user_id,
        )

        assert result.body == "Hello world"
        # author_id is injected from the authenticated user, not the payload.
        mock_comment_repository.create.assert_awaited_once()
        _args, kwargs = mock_comment_repository.create.await_args
        assert kwargs["author_id"] == sample_user_id
        mock_team_service.require_team_access.assert_awaited_once_with(
            sample_user_id, sample_team_id, min_role=TeamRole.member
        )

    @pytest.mark.asyncio
    async def test_empty_body_rejected_422(
        self, service, mock_issue_repository, mock_team_service,
        issue_obj, issue_id, sample_user_id, sample_team_id,
    ):
        """Empty/whitespace-only body is rejected (VAL-COMMENTS-002)."""
        mock_issue_repository.get.return_value = issue_obj
        with pytest.raises(HTTPException) as exc:
            await service.create(
                CommentCreate(issue_id=issue_id, body="   "),
                user_id=sample_user_id,
            )
        assert exc.value.status_code == 422
        service.repo.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_guest_blocked_from_create(
        self, service, mock_issue_repository, mock_team_service,
        issue_obj, issue_id, sample_user_id, sample_team_id,
    ):
        """A guest cannot comment (403) — member role required (VAL-CROSS-025)."""
        mock_issue_repository.get.return_value = issue_obj
        mock_team_service.require_team_access.side_effect = ForbiddenError(detail="no")

        with pytest.raises(ForbiddenError):
            await service.create(
                CommentCreate(issue_id=issue_id, body="Hi"),
                user_id=sample_user_id,
            )
        service.repo.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_cross_team_issue_rejected_404(
        self, service, mock_issue_repository, issue_id, sample_user_id,
    ):
        """Commenting on a foreign-team issue raises 404 (no leak)."""
        mock_issue_repository.get.return_value = None
        with pytest.raises(NotFoundError):
            await service.create(
                CommentCreate(issue_id=issue_id, body="Hi"),
                user_id=sample_user_id,
            )


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


class TestList:
    @pytest.mark.asyncio
    async def test_list_scoped_to_issue_returns_thread(
        self, service, mock_team_service, mock_issue_repository,
        mock_comment_repository, issue_obj, comment_obj,
        issue_id, sample_user_id, sample_team_id,
    ):
        """Listing by issue_id returns the comment thread (VAL-COMMENTS-003)."""
        mock_team_service.get_team_ids_for_user.return_value = [sample_team_id]
        mock_issue_repository.get.return_value = issue_obj
        mock_comment_repository.get_all_paginated.return_value = SimpleNamespace(
            items=[comment_obj], total=1, page=1, size=50, pages=1
        )

        result = await service.get_all_paginated(
            Params(), user_id=sample_user_id, issue_id=issue_id
        )
        assert result.total == 1
        mock_issue_repository.get.assert_awaited_with(issue_id, raise_error=False)

    @pytest.mark.asyncio
    async def test_list_cross_team_issue_404(
        self, service, mock_team_service, issue_id, sample_user_id, other_team_id,
    ):
        """Listing a foreign-team issue's comments raises 404 (no leak)."""
        mock_team_service.get_team_ids_for_user.return_value = [other_team_id]
        with pytest.raises(NotFoundError):
            await service.get_all_paginated(
                Params(), user_id=sample_user_id, issue_id=issue_id
            )


# ---------------------------------------------------------------------------
# Update (author / admin)
# ---------------------------------------------------------------------------


class TestUpdate:
    @pytest.mark.asyncio
    async def test_author_can_edit(
        self, service, mock_comment_repository, mock_issue_repository,
        mock_team_service, comment_obj, issue_obj, comment_id, issue_id,
        sample_user_id, sample_team_id,
    ):
        """The author can edit their comment in place (VAL-COMMENTS-005)."""
        mock_team_service.get_team_ids_for_user.return_value = [sample_team_id]
        mock_comment_repository.get.return_value = comment_obj
        mock_issue_repository.get.return_value = issue_obj
        updated = SimpleNamespace(**{**comment_obj.__dict__, "body": "Edited"})
        mock_comment_repository.update.return_value = updated

        result = await service.update(
            comment_id,
            CommentUpdate(body="Edited"),
            user_id=sample_user_id,
        )
        assert result.body == "Edited"
        mock_comment_repository.update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_non_author_member_blocked(
        self, service, mock_comment_repository, mock_issue_repository,
        mock_team_service, comment_obj, issue_obj, comment_id, other_user_id,
        sample_team_id,
    ):
        """A non-author member cannot edit (403) (VAL-COMMENTS-008)."""
        # Comment authored by sample_user_id; caller is other_user_id (a member).
        mock_team_service.get_team_ids_for_user.return_value = [sample_team_id]
        mock_comment_repository.get.return_value = comment_obj
        mock_issue_repository.get.return_value = issue_obj
        mock_team_service.get_role_map_for_user.return_value = {
            sample_team_id: TeamRole.member
        }

        with pytest.raises(ForbiddenError):
            await service.update(
                comment_id,
                CommentUpdate(body="hacked"),
                user_id=other_user_id,
            )
        mock_comment_repository.update.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_admin_can_edit_others(
        self, service, mock_comment_repository, mock_issue_repository,
        mock_team_service, comment_obj, issue_obj, comment_id, other_user_id,
        sample_team_id,
    ):
        """A team admin can edit any comment (VAL-COMMENTS-008)."""
        mock_team_service.get_team_ids_for_user.return_value = [sample_team_id]
        mock_comment_repository.get.return_value = comment_obj
        mock_issue_repository.get.return_value = issue_obj
        mock_team_service.get_role_map_for_user.return_value = {
            sample_team_id: TeamRole.admin
        }
        updated = SimpleNamespace(**{**comment_obj.__dict__, "body": "admin edit"})
        mock_comment_repository.update.return_value = updated

        result = await service.update(
            comment_id,
            CommentUpdate(body="admin edit"),
            user_id=other_user_id,
        )
        assert result.body == "admin edit"

    @pytest.mark.asyncio
    async def test_empty_body_rejected_422(
        self, service, mock_comment_repository, mock_issue_repository,
        mock_team_service, comment_obj, issue_obj, comment_id, sample_user_id,
        sample_team_id,
    ):
        """Editing to an empty/whitespace body is rejected (VAL-COMMENTS-002)."""
        mock_team_service.get_team_ids_for_user.return_value = [sample_team_id]
        mock_comment_repository.get.return_value = comment_obj
        mock_issue_repository.get.return_value = issue_obj

        with pytest.raises(HTTPException) as exc:
            await service.update(
                comment_id,
                CommentUpdate(body="   "),
                user_id=sample_user_id,
            )
        assert exc.value.status_code == 422
        mock_comment_repository.update.assert_not_awaited()


# ---------------------------------------------------------------------------
# Delete (author / admin)
# ---------------------------------------------------------------------------


class TestDelete:
    @pytest.mark.asyncio
    async def test_author_can_delete(
        self, service, mock_comment_repository, mock_issue_repository,
        mock_team_service, comment_obj, issue_obj, comment_id, sample_user_id,
        sample_team_id,
    ):
        """The author can delete their comment (VAL-COMMENTS-006)."""
        mock_team_service.get_team_ids_for_user.return_value = [sample_team_id]
        mock_comment_repository.get.return_value = comment_obj
        mock_issue_repository.get.return_value = issue_obj

        await service.delete(comment_id, user_id=sample_user_id)
        mock_comment_repository.delete.assert_awaited_once_with(comment_id)

    @pytest.mark.asyncio
    async def test_admin_can_delete_others(
        self, service, mock_comment_repository, mock_issue_repository,
        mock_team_service, comment_obj, issue_obj, comment_id, other_user_id,
        sample_team_id,
    ):
        """A team admin can delete any comment (VAL-COMMENTS-008)."""
        mock_team_service.get_team_ids_for_user.return_value = [sample_team_id]
        mock_comment_repository.get.return_value = comment_obj
        mock_issue_repository.get.return_value = issue_obj
        mock_team_service.get_role_map_for_user.return_value = {
            sample_team_id: TeamRole.admin
        }

        await service.delete(comment_id, user_id=other_user_id)
        mock_comment_repository.delete.assert_awaited_once_with(comment_id)

    @pytest.mark.asyncio
    async def test_non_author_member_blocked(
        self, service, mock_comment_repository, mock_issue_repository,
        mock_team_service, comment_obj, issue_obj, comment_id, other_user_id,
        sample_team_id,
    ):
        """A non-author member cannot delete (403) (VAL-COMMENTS-008)."""
        mock_team_service.get_team_ids_for_user.return_value = [sample_team_id]
        mock_comment_repository.get.return_value = comment_obj
        mock_issue_repository.get.return_value = issue_obj
        mock_team_service.get_role_map_for_user.return_value = {
            sample_team_id: TeamRole.member
        }

        with pytest.raises(ForbiddenError):
            await service.delete(comment_id, user_id=other_user_id)
        mock_comment_repository.delete.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_cross_team_comment_404(
        self, service, mock_team_service, mock_comment_repository,
        comment_obj, comment_id, sample_user_id, other_team_id,
    ):
        """Deleting a foreign-team comment raises 404 (no leak)."""
        mock_comment_repository.get.return_value = comment_obj
        mock_team_service.get_team_ids_for_user.return_value = [other_team_id]

        with pytest.raises(NotFoundError):
            await service.delete(comment_id, user_id=sample_user_id)
