"""Tests for ViewService (team-scoped, member-write, owner injected on create)."""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi_pagination import Params

from app.modules.teams.models import TeamRole
from app.modules.views.models import View
from app.modules.views.schemas import ViewCreate, ViewUpdate
from app.modules.views.service import ViewService
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
def view_id():
    return uuid.UUID("55555555-5555-5555-5555-555555555555")


@pytest.fixture
def membership_obj(sample_user_id, sample_team_id):
    return SimpleNamespace(
        id=uuid.UUID("77777777-0000-0000-0000-000000000000"),
        user_id=sample_user_id,
        team_id=sample_team_id,
        role=TeamRole.member,
    )


@pytest.fixture
def view_obj(view_id, sample_team_id, sample_user_id):
    return SimpleNamespace(
        id=view_id,
        owner_id=sample_user_id,
        team_id=sample_team_id,
        name="Urgent bugs",
        filters={"status_id": "abc", "priority": 0},
        group_by="status",
        order_by="priority",
        description=None,
    )


@pytest.fixture
def service(mock_view_repository, mock_team_service):
    return ViewService(repo=mock_view_repository, team_service=mock_team_service)


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestViewModel:
    def test_view_table_registered(self):
        from app.database.base import Base

        assert "view" in Base.metadata.tables

    def test_view_model_fields(self):
        cols = {c.name for c in View.__table__.columns}
        assert {
            "id",
            "owner_id",
            "team_id",
            "name",
            "filters",
            "group_by",
            "order_by",
            "description",
            "created_at",
            "updated_at",
        } <= cols

    def test_filters_is_jsonb(self):
        """The filters column is a JSONB column (captures filters config)."""
        from sqlalchemy.dialects.postgresql import JSONB

        filters_col = View.__table__.columns["filters"]
        assert isinstance(filters_col.type, JSONB)


# ---------------------------------------------------------------------------
# get_all_paginated
# ---------------------------------------------------------------------------


class TestGetAllPaginated:
    async def test_scopes_to_user_teams(
        self,
        service,
        mock_view_repository,
        mock_team_service,
        sample_user_id,
        sample_team_id,
        view_obj,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_view_repository.get_all_paginated = AsyncMock(
            return_value=SimpleNamespace(
                items=[view_obj], total=1, page=1, size=50, pages=1
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
    async def test_returns_view_for_member(
        self,
        service,
        mock_view_repository,
        mock_team_service,
        sample_user_id,
        sample_team_id,
        view_id,
        view_obj,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_view_repository.get = AsyncMock(return_value=view_obj)

        result = await service.get_by_id(view_id, user_id=sample_user_id)

        assert result == view_obj

    async def test_404_for_other_team_view(
        self,
        service,
        mock_view_repository,
        mock_team_service,
        sample_user_id,
        other_team_id,
        view_id,
        view_obj,
    ):
        view_obj.team_id = other_team_id
        mock_team_service.get_team_ids_for_user = AsyncMock(return_value=[])
        mock_view_repository.get = AsyncMock(return_value=view_obj)

        with pytest.raises(NotFoundError):
            await service.get_by_id(view_id, user_id=sample_user_id)


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


class TestCreate:
    async def test_requires_member_role(
        self,
        service,
        mock_team_service,
        mock_view_repository,
        sample_user_id,
        sample_team_id,
        view_obj,
    ):
        mock_view_repository.create = AsyncMock(return_value=view_obj)

        await service.create(
            ViewCreate(team_id=sample_team_id, name="Urgent bugs"),
            user_id=sample_user_id,
        )

        mock_team_service.require_team_access.assert_awaited_once_with(
            sample_user_id, sample_team_id, min_role=TeamRole.member
        )

    async def test_injects_owner_id_from_user(
        self,
        service,
        mock_team_service,
        mock_view_repository,
        sample_user_id,
        sample_team_id,
        view_obj,
    ):
        """owner_id is injected from the authenticated user, not the client."""
        mock_view_repository.create = AsyncMock(return_value=view_obj)

        await service.create(
            ViewCreate(team_id=sample_team_id, name="Urgent bugs"),
            user_id=sample_user_id,
        )

        mock_view_repository.create.assert_awaited_once()
        _, kwargs = mock_view_repository.create.call_args
        assert kwargs["owner_id"] == sample_user_id

    async def test_403_for_guest(
        self,
        service,
        mock_team_service,
        mock_view_repository,
        sample_user_id,
        sample_team_id,
    ):
        """Guests are read-only — creating a view is forbidden (403)."""
        mock_team_service.require_team_access = AsyncMock(
            side_effect=ForbiddenError(detail="guest cannot write")
        )

        with pytest.raises(ForbiddenError):
            await service.create(
                ViewCreate(team_id=sample_team_id, name="V"),
                user_id=sample_user_id,
            )

        mock_view_repository.create.assert_not_awaited()

    async def test_no_team_id_raises(self, service, sample_user_id):
        from unittest.mock import MagicMock

        mock_entity = MagicMock()
        mock_entity.team_id = None

        with pytest.raises(NotFoundError):
            await service.create(mock_entity, user_id=sample_user_id)

    async def test_captures_filters_group_by_order_by(
        self,
        service,
        mock_team_service,
        mock_view_repository,
        sample_user_id,
        sample_team_id,
        view_obj,
    ):
        """Create captures filters + group_by + order_by (VAL-VIEWS-001)."""
        mock_view_repository.create = AsyncMock(return_value=view_obj)

        await service.create(
            ViewCreate(
                team_id=sample_team_id,
                name="Urgent bugs",
                filters={"status_id": "st-1", "priority": 0},
                group_by="status",
                order_by="priority",
            ),
            user_id=sample_user_id,
        )

        args, _kwargs = mock_view_repository.create.call_args
        entity = args[0]
        assert entity.filters == {"status_id": "st-1", "priority": 0}
        assert entity.group_by == "status"
        assert entity.order_by == "priority"


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


class TestUpdate:
    async def test_update_member_enforced(
        self,
        service,
        mock_team_service,
        mock_view_repository,
        sample_user_id,
        sample_team_id,
        view_id,
        view_obj,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_view_repository.get = AsyncMock(return_value=view_obj)
        mock_view_repository.update = AsyncMock(return_value=view_obj)

        await service.update(
            view_id,
            ViewUpdate(name="Renamed"),
            user_id=sample_user_id,
        )

        mock_team_service.require_team_access.assert_awaited_once_with(
            sample_user_id, sample_team_id, min_role=TeamRole.member
        )

    async def test_403_for_guest(
        self,
        service,
        mock_team_service,
        mock_view_repository,
        sample_user_id,
        sample_team_id,
        view_id,
        view_obj,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_view_repository.get = AsyncMock(return_value=view_obj)
        mock_team_service.require_team_access = AsyncMock(
            side_effect=ForbiddenError(detail="guest cannot write")
        )

        with pytest.raises(ForbiddenError):
            await service.update(
                view_id,
                ViewUpdate(name="X"),
                user_id=sample_user_id,
            )

        mock_view_repository.update.assert_not_awaited()


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


class TestDelete:
    async def test_delete_member_enforced(
        self,
        service,
        mock_team_service,
        mock_view_repository,
        sample_user_id,
        sample_team_id,
        view_id,
        view_obj,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_view_repository.get = AsyncMock(return_value=view_obj)
        mock_view_repository.delete = AsyncMock(return_value=None)

        await service.delete(view_id, user_id=sample_user_id)

        mock_view_repository.delete.assert_awaited_once_with(view_id)

    async def test_404_for_other_team_view(
        self,
        service,
        mock_team_service,
        mock_view_repository,
        sample_user_id,
        other_team_id,
        view_id,
        view_obj,
    ):
        view_obj.team_id = other_team_id
        mock_team_service.get_team_ids_for_user = AsyncMock(return_value=[])
        mock_view_repository.get = AsyncMock(return_value=view_obj)

        with pytest.raises(NotFoundError):
            await service.delete(view_id, user_id=sample_user_id)
