"""Tests for IssueDependencyService (team-scoped, same-team, cycle guard).

Covers:
  - "A blocks B" persists an IssueDependency (VAL-DEPS-001).
  - Reciprocal: both issues see the relationship (VAL-DEPS-002).
  - Circular dependency rejected with 409 (VAL-DEPS-003).
  - Self-dependency rejected (would-be cycle).
  - Cross-team pair rejected (404 — existence not leaked) (VAL-DEPS-005).
  - Team access enforced (member role required for writes).
  - Delete removes the relationship from both sides (VAL-DEPS-004).
  - List scoped by issue_id returns deps involving that issue.
"""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from fastapi_pagination import Params

from app.modules.issue_dependencies.models import IssueDependency
from app.modules.issue_dependencies.schemas import IssueDependencyCreate
from app.modules.issue_dependencies.service import IssueDependencyService
from app.modules.teams.models import TeamRole
from app.repositories.exceptions import ForbiddenError, NotFoundError

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_user_id():
    return uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def sample_team_id():
    return uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
def other_team_id():
    return uuid.UUID("33333333-3333-3333-3333-333333333333")


@pytest.fixture
def issue_a_id():
    return uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


@pytest.fixture
def issue_b_id():
    return uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


@pytest.fixture
def issue_c_id():
    return uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")


@pytest.fixture
def dep_id():
    return uuid.UUID("55555555-5555-5555-5555-555555555555")


@pytest.fixture
def issue_a(issue_a_id, sample_team_id):
    return SimpleNamespace(
        id=issue_a_id,
        team_id=sample_team_id,
        identifier="ENG-1",
        title="Issue A",
        priority=2,
        status_id=uuid.UUID("44444444-4444-4444-4444-444444444444"),
    )


@pytest.fixture
def issue_b(issue_b_id, sample_team_id):
    return SimpleNamespace(
        id=issue_b_id,
        team_id=sample_team_id,
        identifier="ENG-2",
        title="Issue B",
        priority=3,
        status_id=uuid.UUID("44444444-4444-4444-4444-444444444444"),
    )


@pytest.fixture
def issue_c(issue_c_id, sample_team_id):
    return SimpleNamespace(
        id=issue_c_id,
        team_id=sample_team_id,
        identifier="ENG-3",
        title="Issue C",
        priority=1,
        status_id=uuid.UUID("44444444-4444-4444-4444-444444444444"),
    )


@pytest.fixture
def dep_obj(dep_id, issue_a_id, issue_b_id):
    return SimpleNamespace(
        id=dep_id,
        blocker_id=issue_a_id,
        blocked_id=issue_b_id,
        relation="blocks",
        blocker=issue_a_id,  # service tests only care about ids for most paths
        blocked=issue_b_id,
    )


@pytest.fixture
def mock_issue_dependency_repository():
    """Mock IssueDependencyRepository."""
    import unittest.mock as um

    repo = um.MagicMock()
    repo.get = AsyncMock()
    repo.get_by_field = AsyncMock()
    repo.get_all = AsyncMock()
    repo.get_all_paginated = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.get_edges_for_team = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_issue_repository():
    """Mock IssueRepository (for validating referenced issues)."""
    import unittest.mock as um

    repo = um.MagicMock()
    repo.get = AsyncMock()
    return repo


@pytest.fixture
def service(mock_issue_dependency_repository, mock_issue_repository, mock_team_service):
    return IssueDependencyService(
        repo=mock_issue_dependency_repository,
        team_service=mock_team_service,
        issue_repo=mock_issue_repository,
    )


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestIssueDependencyModel:
    def test_table_registered(self):
        from app.database.base import Base

        assert "issue_dependency" in Base.metadata.tables

    def test_model_fields(self):
        cols = {c.name for c in IssueDependency.__table__.columns}
        assert {"id", "blocker_id", "blocked_id", "relation"} <= cols

    def test_compound_unique_constraint(self):
        """A compound unique constraint covers the (blocker_id, blocked_id) pair."""
        constraints = [
            c for c in IssueDependency.__table__.constraints
            if c.__class__.__name__ == "UniqueConstraint"
        ]
        colnames = []
        for c in constraints:
            colnames.append(sorted(col.name for col in c.columns))
        assert sorted(["blocker_id", "blocked_id"]) in colnames


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


class TestCreate:
    @pytest.mark.asyncio
    async def test_creates_a_blocks_b(
        self, service, mock_issue_repository, mock_issue_dependency_repository,
        mock_team_service, issue_a, issue_b, issue_a_id, issue_b_id,
        sample_team_id, sample_user_id, dep_obj,
    ):
        """'A blocks B' persists IssueDependency(blocker=A, blocked=B) (VAL-DEPS-001)."""
        mock_issue_repository.get.side_effect = [issue_a, issue_b]
        mock_issue_dependency_repository.get_edges_for_team.return_value = []
        mock_issue_dependency_repository.create.return_value = dep_obj
        mock_issue_dependency_repository.get.return_value = dep_obj

        result = await service.create(
            IssueDependencyCreate(blocker_id=issue_a_id, blocked_id=issue_b_id),
            user_id=sample_user_id,
        )

        assert result.blocker_id == issue_a_id
        assert result.blocked_id == issue_b_id
        mock_team_service.require_team_access.assert_awaited_once_with(
            sample_user_id, sample_team_id, min_role=TeamRole.member
        )

    @pytest.mark.asyncio
    async def test_self_dependency_rejected(
        self, service, issue_a_id, sample_user_id,
    ):
        """An issue cannot block itself (would be a trivial cycle)."""
        with pytest.raises(HTTPException) as exc:
            await service.create(
                IssueDependencyCreate(blocker_id=issue_a_id, blocked_id=issue_a_id),
                user_id=sample_user_id,
            )
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_cycle_rejected_409(
        self, service, mock_issue_repository,
        mock_issue_dependency_repository, issue_a, issue_b,
        issue_a_id, issue_b_id, sample_team_id, sample_user_id,
    ):
        """After 'A blocks B', 'B blocks A' is rejected with 409 (VAL-DEPS-003).

        Creating blocker=B, blocked=A: existing edge A->B means A can reach the
        new blocker B through the chain, forming a cycle.
        """
        mock_issue_repository.get.side_effect = [issue_b, issue_a]
        # Existing edge: A blocks B  (blocker=A, blocked=B)
        mock_issue_dependency_repository.get_edges_for_team.return_value = [
            (issue_a_id, issue_b_id),
        ]

        with pytest.raises(HTTPException) as exc:
            await service.create(
                IssueDependencyCreate(blocker_id=issue_b_id, blocked_id=issue_a_id),
                user_id=sample_user_id,
            )
        assert exc.value.status_code == 409
        mock_issue_dependency_repository.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_longer_cycle_rejected_409(
        self, service, mock_issue_repository,
        mock_issue_dependency_repository, issue_a, issue_b, issue_c,
        issue_a_id, issue_b_id, issue_c_id, sample_user_id,
    ):
        """A->B, B->C exist; creating C->A is rejected (3-cycle) (VAL-DEPS-003)."""
        mock_issue_repository.get.side_effect = [issue_c, issue_a]
        mock_issue_dependency_repository.get_edges_for_team.return_value = [
            (issue_a_id, issue_b_id),
            (issue_b_id, issue_c_id),
        ]

        with pytest.raises(HTTPException) as exc:
            await service.create(
                IssueDependencyCreate(blocker_id=issue_c_id, blocked_id=issue_a_id),
                user_id=sample_user_id,
            )
        assert exc.value.status_code == 409

    @pytest.mark.asyncio
    async def test_non_cycle_allowed(
        self, service, mock_issue_repository,
        mock_issue_dependency_repository, issue_a, issue_b, issue_c,
        issue_a_id, issue_b_id, issue_c_id, sample_team_id, sample_user_id, dep_obj,
    ):
        """A->B exists; creating B->C is allowed (no cycle)."""
        mock_issue_repository.get.side_effect = [issue_b, issue_c]
        mock_issue_dependency_repository.get_edges_for_team.return_value = [
            (issue_a_id, issue_b_id),
        ]
        mock_issue_dependency_repository.create.return_value = dep_obj
        mock_issue_dependency_repository.get.return_value = dep_obj

        result = await service.create(
            IssueDependencyCreate(blocker_id=issue_b_id, blocked_id=issue_c_id),
            user_id=sample_user_id,
        )
        assert result is dep_obj

    @pytest.mark.asyncio
    async def test_cross_team_pair_rejected_404(
        self, service, mock_issue_repository, issue_a, issue_b,
        issue_a_id, issue_b_id, other_team_id, sample_user_id,
    ):
        """A pair spanning two teams is rejected with 404 (VAL-DEPS-005)."""
        foreign_b = SimpleNamespace(
            id=issue_b_id, team_id=other_team_id, identifier="X-2",
            title="B", priority=3, status_id=issue_b.status_id,
        )
        mock_issue_repository.get.side_effect = [issue_a, foreign_b]
        with pytest.raises(NotFoundError):
            await service.create(
                IssueDependencyCreate(blocker_id=issue_a_id, blocked_id=issue_b_id),
                user_id=sample_user_id,
            )

    @pytest.mark.asyncio
    async def test_missing_issue_rejected_404(
        self, service, mock_issue_repository, issue_a,
        issue_a_id, issue_b_id, sample_user_id,
    ):
        """A non-existent referenced issue raises 404 (no leak)."""
        mock_issue_repository.get.side_effect = [issue_a, None]
        with pytest.raises(NotFoundError):
            await service.create(
                IssueDependencyCreate(blocker_id=issue_a_id, blocked_id=issue_b_id),
                user_id=sample_user_id,
            )

    @pytest.mark.asyncio
    async def test_guest_blocked_from_create(
        self, service, mock_issue_repository, mock_team_service,
        issue_a, issue_b, issue_a_id, issue_b_id, sample_team_id, sample_user_id,
    ):
        """A guest is blocked from creating dependencies (403) (VAL-CROSS-025)."""
        mock_issue_repository.get.side_effect = [issue_a, issue_b]
        mock_team_service.require_team_access.side_effect = ForbiddenError(detail="no")

        with pytest.raises(ForbiddenError):
            await service.create(
                IssueDependencyCreate(blocker_id=issue_a_id, blocked_id=issue_b_id),
                user_id=sample_user_id,
            )
        mock_issue_dependency_repository = service.repo
        mock_issue_dependency_repository.create.assert_not_awaited()


# ---------------------------------------------------------------------------
# Reciprocal / List
# ---------------------------------------------------------------------------


class TestList:
    @pytest.mark.asyncio
    async def test_list_scoped_to_issue_returns_both_sides(
        self, service, mock_issue_repository, mock_issue_dependency_repository,
        mock_team_service, issue_a, issue_a_id, sample_user_id, sample_team_id, dep_obj,
    ):
        """Listing by issue_id returns deps where the issue is either side
        (VAL-DEPS-002 reciprocal). The service validates the issue is visible to
        the caller (no cross-team leak) before listing."""
        from types import SimpleNamespace

        mock_team_service.get_team_ids_for_user.return_value = [sample_team_id]
        mock_issue_repository.get.return_value = issue_a
        mock_issue_dependency_repository.get_all_paginated.return_value = SimpleNamespace(
            items=[dep_obj], total=1, page=1, size=50, pages=1
        )

        result = await service.get_all_paginated(
            Params(),
            user_id=sample_user_id,
            issue_id=issue_a_id,
        )
        assert result.total == 1
        # The issue_id path resolves the issue to confirm team visibility.
        mock_issue_repository.get.assert_awaited_with(
            issue_a_id, raise_error=False
        )

    @pytest.mark.asyncio
    async def test_list_cross_team_issue_404(
        self, service, mock_team_service, issue_a_id, sample_user_id, other_team_id,
    ):
        """Listing a foreign-team issue raises 404 (no leak)."""
        mock_team_service.get_team_ids_for_user.return_value = [other_team_id]
        with pytest.raises(NotFoundError):
            await service.get_all_paginated(
                Params(), user_id=sample_user_id, issue_id=issue_a_id,
            )


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


class TestDelete:
    @pytest.mark.asyncio
    async def test_delete_removes_from_both_sides(
        self, service, mock_issue_repository, mock_issue_dependency_repository,
        mock_team_service, dep_obj, dep_id, issue_a, issue_b,
        sample_user_id, sample_team_id,
    ):
        """Deleting a dependency removes it for both issues (VAL-DEPS-004)."""
        mock_issue_dependency_repository.get.return_value = dep_obj
        mock_team_service.get_team_ids_for_user.return_value = [sample_team_id]
        # get_by_id resolves both endpoints via issue_repo.get.
        mock_issue_repository.get.side_effect = [issue_a, issue_b, issue_a]

        await service.delete(dep_id, user_id=sample_user_id)

        mock_issue_dependency_repository.delete.assert_awaited_once_with(dep_id)

    @pytest.mark.asyncio
    async def test_delete_cross_team_404(
        self, service, mock_issue_dependency_repository, mock_team_service,
        mock_issue_repository, dep_obj, dep_id, sample_user_id, sample_team_id,
        other_team_id,
    ):
        """Deleting a dependency in a foreign team raises 404."""
        foreign_issue = SimpleNamespace(
            id=dep_obj.blocker_id, team_id=other_team_id, identifier="X-1",
            title="X", priority=0, status_id=uuid.UUID("44444444-4444-4444-4444-444444444444"),
        )
        mock_issue_dependency_repository.get.return_value = dep_obj
        # The user is a member of sample_team_id, NOT other_team_id.
        mock_team_service.get_team_ids_for_user.return_value = [sample_team_id]
        mock_issue_repository.get.return_value = foreign_issue

        with pytest.raises(NotFoundError):
            await service.delete(dep_id, user_id=sample_user_id)
