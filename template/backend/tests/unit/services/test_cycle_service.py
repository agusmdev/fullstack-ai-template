"""Tests for CycleService (team-scoped, member-write, date-window validation)."""

import uuid
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from fastapi_pagination import Params

from app.modules.cycles.models import Cycle
from app.modules.cycles.schemas import CycleCreate, CycleUpdate
from app.modules.cycles.service import CycleService
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
def cycle_id():
    return uuid.UUID("66666666-6666-6666-6666-666666666666")


@pytest.fixture
def cycle_obj(cycle_id, sample_team_id):
    return SimpleNamespace(
        id=cycle_id,
        team_id=sample_team_id,
        name="Sprint 1",
        starts_at=date(2026, 8, 1),
        ends_at=date(2026, 8, 14),
        completed_at=None,
    )


@pytest.fixture
def service(mock_cycle_repository, mock_team_service):
    return CycleService(repo=mock_cycle_repository, team_service=mock_team_service)


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestCycleModel:
    def test_cycle_table_registered(self):
        from app.database.base import Base

        assert "cycle" in Base.metadata.tables

    def test_cycle_model_fields(self):
        cols = {c.name for c in Cycle.__table__.columns}
        assert {
            "id",
            "team_id",
            "name",
            "starts_at",
            "ends_at",
            "completed_at",
            "created_at",
            "updated_at",
        } <= cols

    def test_cycle_completed_at_nullable(self):
        """completed_at is nullable (active/upcoming cycles have no completion)."""
        from sqlalchemy import inspect as sa_inspect

        completed_col = sa_inspect(Cycle).columns["completed_at"]
        assert completed_col.nullable is True

    def test_cycle_starts_ends_not_nullable(self):
        """starts_at and ends_at are required (not nullable)."""
        from sqlalchemy import inspect as sa_inspect

        assert sa_inspect(Cycle).columns["starts_at"].nullable is False
        assert sa_inspect(Cycle).columns["ends_at"].nullable is False


# ---------------------------------------------------------------------------
# Schema tests (date-window validation)
# ---------------------------------------------------------------------------


class TestCycleSchemas:
    def test_create_requires_name_start_end(self):
        """All three fields are required for a valid cycle create (VAL-CYCLES-001)."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CycleCreate(team_id=sample_team_id_value())

    def test_rejects_end_before_start(self):
        """end ≤ start is rejected with a validation error (VAL-CYCLES-002)."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CycleCreate(
                team_id=sample_team_id_value(),
                name="Sprint",
                starts_at=date(2026, 8, 14),
                ends_at=date(2026, 8, 1),
            )

    def test_rejects_end_equal_start(self):
        """end == start is also rejected (must be strictly after)."""
        from pydantic import ValidationError

        same = date(2026, 8, 10)
        with pytest.raises(ValidationError):
            CycleCreate(
                team_id=sample_team_id_value(),
                name="Sprint",
                starts_at=same,
                ends_at=same,
            )

    def test_accepts_valid_window(self):
        """A valid date range (end > start) is accepted."""
        cycle = CycleCreate(
            team_id=sample_team_id_value(),
            name="Sprint",
            starts_at=date(2026, 8, 1),
            ends_at=date(2026, 8, 14),
        )
        assert cycle.starts_at < cycle.ends_at

    def test_rejects_blank_name(self):
        """Whitespace-only name is rejected."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CycleCreate(
                team_id=sample_team_id_value(),
                name="   ",
                starts_at=date(2026, 8, 1),
                ends_at=date(2026, 8, 14),
            )


# ---------------------------------------------------------------------------
# get_all_paginated
# ---------------------------------------------------------------------------


class TestGetAllPaginated:
    async def test_scopes_to_user_teams(
        self,
        service,
        mock_cycle_repository,
        mock_team_service,
        sample_user_id,
        sample_team_id,
        cycle_obj,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_cycle_repository.get_all_paginated = AsyncMock(
            return_value=SimpleNamespace(
                items=[cycle_obj], total=1, page=1, size=50, pages=1
            )
        )

        result = await service.get_all_paginated(Params(), user_id=sample_user_id)

        assert result.total == 1

    async def test_team_id_filter_404_for_non_member(
        self,
        service,
        mock_team_service,
        sample_user_id,
        other_team_id,
        sample_team_id,
    ):
        """A user filtering by a team they don't belong to gets 404 (no leak)."""
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )

        with pytest.raises(NotFoundError):
            await service.get_all_paginated(
                Params(), user_id=sample_user_id, team_id=other_team_id
            )


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------


class TestGetById:
    async def test_returns_cycle_for_member(
        self,
        service,
        mock_cycle_repository,
        mock_team_service,
        sample_user_id,
        sample_team_id,
        cycle_id,
        cycle_obj,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_cycle_repository.get = AsyncMock(return_value=cycle_obj)

        result = await service.get_by_id(cycle_id, user_id=sample_user_id)

        assert result == cycle_obj

    async def test_404_for_other_team_cycle(
        self,
        service,
        mock_cycle_repository,
        mock_team_service,
        sample_user_id,
        other_team_id,
        cycle_id,
        cycle_obj,
    ):
        cycle_obj.team_id = other_team_id
        mock_team_service.get_team_ids_for_user = AsyncMock(return_value=[])
        mock_cycle_repository.get = AsyncMock(return_value=cycle_obj)

        with pytest.raises(NotFoundError):
            await service.get_by_id(cycle_id, user_id=sample_user_id)


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


class TestCreate:
    async def test_requires_member_role(
        self,
        service,
        mock_team_service,
        mock_cycle_repository,
        sample_user_id,
        sample_team_id,
        cycle_obj,
    ):
        mock_cycle_repository.create = AsyncMock(return_value=cycle_obj)

        await service.create(
            CycleCreate(
                team_id=sample_team_id,
                name="Sprint 1",
                starts_at=date(2026, 8, 1),
                ends_at=date(2026, 8, 14),
            ),
            user_id=sample_user_id,
        )

        mock_team_service.require_team_access.assert_awaited_once_with(
            sample_user_id, sample_team_id, min_role=TeamRole.member
        )

    async def test_403_for_guest(
        self,
        service,
        mock_team_service,
        mock_cycle_repository,
        sample_user_id,
        sample_team_id,
    ):
        """Guests are read-only — creating a cycle is forbidden (403)."""
        mock_team_service.require_team_access = AsyncMock(
            side_effect=ForbiddenError(detail="guest cannot write")
        )

        with pytest.raises(ForbiddenError):
            await service.create(
                CycleCreate(
                    team_id=sample_team_id,
                    name="Sprint",
                    starts_at=date(2026, 8, 1),
                    ends_at=date(2026, 8, 14),
                ),
                user_id=sample_user_id,
            )

        mock_cycle_repository.create.assert_not_awaited()

    async def test_no_team_id_raises(self, service, sample_user_id):
        from unittest.mock import MagicMock

        mock_entity = MagicMock()
        mock_entity.team_id = None

        with pytest.raises(NotFoundError):
            await service.create(mock_entity, user_id=sample_user_id)


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


class TestUpdate:
    async def test_update_member_enforced(
        self,
        service,
        mock_team_service,
        mock_cycle_repository,
        sample_user_id,
        sample_team_id,
        cycle_id,
        cycle_obj,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_cycle_repository.get = AsyncMock(return_value=cycle_obj)
        mock_cycle_repository.update = AsyncMock(return_value=cycle_obj)

        await service.update(
            cycle_id,
            CycleUpdate(name="Renamed Sprint"),
            user_id=sample_user_id,
        )

        mock_team_service.require_team_access.assert_awaited_once_with(
            sample_user_id, sample_team_id, min_role=TeamRole.member
        )

    async def test_422_when_partial_end_before_stored_start(
        self,
        service,
        mock_team_service,
        mock_cycle_repository,
        sample_user_id,
        sample_team_id,
        cycle_id,
        cycle_obj,
    ):
        """Updating only ends_at to before the stored starts_at raises 422."""
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_cycle_repository.get = AsyncMock(return_value=cycle_obj)
        # cycle_obj.starts_at = 2026-08-01; setting ends_at to 2026-07-01 < start.
        with pytest.raises(HTTPException) as exc_info:
            await service.update(
                cycle_id,
                CycleUpdate(ends_at=date(2026, 7, 1)),
                user_id=sample_user_id,
            )
        assert exc_info.value.status_code == 422
        mock_cycle_repository.update.assert_not_awaited()

    async def test_partial_update_valid_window_accepted(
        self,
        service,
        mock_team_service,
        mock_cycle_repository,
        sample_user_id,
        sample_team_id,
        cycle_id,
        cycle_obj,
    ):
        """Updating only ends_at (keeping stored start) with a valid window works."""
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_cycle_repository.get = AsyncMock(return_value=cycle_obj)
        mock_cycle_repository.update = AsyncMock(return_value=cycle_obj)

        await service.update(
            cycle_id,
            CycleUpdate(ends_at=date(2026, 8, 20)),
            user_id=sample_user_id,
        )

        mock_cycle_repository.update.assert_awaited_once()


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


class TestDelete:
    async def test_delete_member_enforced(
        self,
        service,
        mock_team_service,
        mock_cycle_repository,
        sample_user_id,
        sample_team_id,
        cycle_id,
        cycle_obj,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_cycle_repository.get = AsyncMock(return_value=cycle_obj)
        mock_cycle_repository.delete = AsyncMock(return_value=None)

        await service.delete(cycle_id, user_id=sample_user_id)

        mock_cycle_repository.delete.assert_awaited_once_with(cycle_id)

    async def test_404_for_other_team_cycle(
        self,
        service,
        mock_team_service,
        mock_cycle_repository,
        sample_user_id,
        other_team_id,
        cycle_id,
        cycle_obj,
    ):
        cycle_obj.team_id = other_team_id
        mock_team_service.get_team_ids_for_user = AsyncMock(return_value=[])
        mock_cycle_repository.get = AsyncMock(return_value=cycle_obj)

        with pytest.raises(NotFoundError):
            await service.delete(cycle_id, user_id=sample_user_id)


# Helper used by schema tests (avoids fixture scope issues with plain values).
def sample_team_id_value() -> uuid.UUID:
    return uuid.UUID("22222222-2222-2222-2222-222222222222")
