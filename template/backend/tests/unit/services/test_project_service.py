"""Tests for ProjectService (team-scoped, member-write, lead validation)."""

import uuid
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi_pagination import Params

from app.modules.projects.models import Project, ProjectStatus
from app.modules.projects.schemas import ProjectCreate, ProjectUpdate
from app.modules.projects.service import ProjectService
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
def lead_id():
    return uuid.UUID("44444444-4444-4444-4444-444444444444")


@pytest.fixture
def project_id():
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
def project_obj(project_id, sample_team_id):
    return SimpleNamespace(
        id=project_id,
        team_id=sample_team_id,
        name="Q3 Launch",
        status=ProjectStatus.planned,
        lead_id=None,
        target_date=None,
        description=None,
    )


@pytest.fixture
def service(mock_project_repository, mock_team_service):
    return ProjectService(repo=mock_project_repository, team_service=mock_team_service)


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestProjectModel:
    def test_project_table_registered(self):
        from app.database.base import Base

        assert "project" in Base.metadata.tables

    def test_project_model_fields(self):
        cols = {c.name for c in Project.__table__.columns}
        assert {
            "id",
            "team_id",
            "name",
            "status",
            "lead_id",
            "target_date",
            "description",
            "created_at",
            "updated_at",
        } <= cols

    def test_project_status_default_is_non_terminal(self):
        """New projects default to a non-terminal status (planned)."""
        from sqlalchemy import inspect as sa_inspect

        status_col = sa_inspect(Project).columns["status"]
        assert status_col.default.arg is ProjectStatus.planned
        assert ProjectStatus.planned in {
            ProjectStatus.planned,
            ProjectStatus.started,
        }


# ---------------------------------------------------------------------------
# get_all_paginated
# ---------------------------------------------------------------------------


class TestGetAllPaginated:
    async def test_scopes_to_user_teams(
        self,
        service,
        mock_project_repository,
        mock_team_service,
        sample_user_id,
        sample_team_id,
        project_obj,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_project_repository.get_all_paginated = AsyncMock(
            return_value=SimpleNamespace(
                items=[project_obj], total=1, page=1, size=50, pages=1
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

    async def test_other_team_project_not_visible(
        self,
        service,
        mock_project_repository,
        mock_team_service,
        sample_user_id,
        other_team_id,
        sample_team_id,
        project_obj,
    ):
        """User in team A does not see team B's projects (team scoping)."""
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_project_repository.get_all_paginated = AsyncMock(
            return_value=SimpleNamespace(items=[], total=0, page=1, size=50, pages=1)
        )

        result = await service.get_all_paginated(
            Params(), user_id=sample_user_id, team_id=sample_team_id
        )

        assert result.total == 0


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------


class TestGetById:
    async def test_returns_project_for_member(
        self,
        service,
        mock_project_repository,
        mock_team_service,
        sample_user_id,
        sample_team_id,
        project_id,
        project_obj,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_project_repository.get = AsyncMock(return_value=project_obj)

        result = await service.get_by_id(project_id, user_id=sample_user_id)

        assert result == project_obj

    async def test_404_for_other_team_project(
        self,
        service,
        mock_project_repository,
        mock_team_service,
        sample_user_id,
        other_team_id,
        project_id,
        project_obj,
    ):
        project_obj.team_id = other_team_id
        mock_team_service.get_team_ids_for_user = AsyncMock(return_value=[])
        mock_project_repository.get = AsyncMock(return_value=project_obj)

        with pytest.raises(NotFoundError):
            await service.get_by_id(project_id, user_id=sample_user_id)


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


class TestCreate:
    async def test_requires_member_role(
        self,
        service,
        mock_team_service,
        mock_project_repository,
        sample_user_id,
        sample_team_id,
        project_obj,
    ):
        mock_project_repository.create = AsyncMock(return_value=project_obj)

        await service.create(
            ProjectCreate(team_id=sample_team_id, name="Q3 Launch"),
            user_id=sample_user_id,
        )

        mock_team_service.require_team_access.assert_awaited_once_with(
            sample_user_id, sample_team_id, min_role=TeamRole.member
        )

    async def test_403_for_guest(
        self,
        service,
        mock_team_service,
        mock_project_repository,
        sample_user_id,
        sample_team_id,
    ):
        """Guests are read-only — creating a project is forbidden (403)."""
        mock_team_service.require_team_access = AsyncMock(
            side_effect=ForbiddenError(detail="guest cannot write")
        )

        with pytest.raises(ForbiddenError):
            await service.create(
                ProjectCreate(team_id=sample_team_id, name="P"),
                user_id=sample_user_id,
            )

        mock_project_repository.create.assert_not_awaited()

    async def test_no_team_id_raises(
        self,
        service,
        sample_user_id,
    ):
        from unittest.mock import MagicMock

        mock_entity = MagicMock()
        mock_entity.team_id = None

        with pytest.raises(NotFoundError):
            await service.create(mock_entity, user_id=sample_user_id)

    async def test_validates_lead_is_team_member(
        self,
        service,
        mock_team_service,
        mock_project_repository,
        sample_user_id,
        sample_team_id,
        lead_id,
        project_obj,
        membership_obj,
    ):
        """A lead that is a team member is accepted."""
        mock_team_service.get_membership = AsyncMock(return_value=membership_obj)
        mock_project_repository.create = AsyncMock(return_value=project_obj)

        await service.create(
            ProjectCreate(team_id=sample_team_id, name="P", lead_id=lead_id),
            user_id=sample_user_id,
        )

        mock_team_service.get_membership.assert_awaited_once_with(
            lead_id, sample_team_id
        )
        mock_project_repository.create.assert_awaited_once()

    async def test_rejects_non_member_lead(
        self,
        service,
        mock_team_service,
        mock_project_repository,
        sample_user_id,
        sample_team_id,
        lead_id,
    ):
        """A lead who is not a team member is rejected on create (404)."""
        mock_team_service.get_membership = AsyncMock(return_value=None)

        with pytest.raises(NotFoundError):
            await service.create(
                ProjectCreate(team_id=sample_team_id, name="P", lead_id=lead_id),
                user_id=sample_user_id,
            )

        mock_project_repository.create.assert_not_awaited()

    async def test_defaults_status_planned(
        self,
        service,
        mock_team_service,
        mock_project_repository,
        sample_user_id,
        sample_team_id,
        project_obj,
    ):
        """Creating without an explicit status defaults to planned (non-terminal)."""
        mock_project_repository.create = AsyncMock(return_value=project_obj)

        await service.create(
            ProjectCreate(team_id=sample_team_id, name="P"),
            user_id=sample_user_id,
        )

        args, _kwargs = mock_project_repository.create.call_args
        # The entity passed to create carries the default status.
        assert args[0].status == ProjectStatus.planned

    async def test_accepts_explicit_status(
        self,
        service,
        mock_team_service,
        mock_project_repository,
        sample_user_id,
        sample_team_id,
        project_obj,
    ):
        """Creating with an explicit status persists it."""
        mock_project_repository.create = AsyncMock(return_value=project_obj)

        await service.create(
            ProjectCreate(
                team_id=sample_team_id, name="P", status=ProjectStatus.started
            ),
            user_id=sample_user_id,
        )

        args, _kwargs = mock_project_repository.create.call_args
        assert args[0].status == ProjectStatus.started

    async def test_accepts_target_date(
        self,
        service,
        mock_team_service,
        mock_project_repository,
        sample_user_id,
        sample_team_id,
        project_obj,
    ):
        """A target date is stored."""
        target = date(2026, 12, 31)
        mock_project_repository.create = AsyncMock(return_value=project_obj)

        await service.create(
            ProjectCreate(team_id=sample_team_id, name="P", target_date=target),
            user_id=sample_user_id,
        )

        args, _kwargs = mock_project_repository.create.call_args
        assert args[0].target_date == target


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


class TestUpdate:
    async def test_update_member_enforced(
        self,
        service,
        mock_team_service,
        mock_project_repository,
        sample_user_id,
        sample_team_id,
        project_id,
        project_obj,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_project_repository.get = AsyncMock(return_value=project_obj)
        mock_project_repository.update = AsyncMock(return_value=project_obj)

        await service.update(
            project_id,
            ProjectUpdate(name="Renamed"),
            user_id=sample_user_id,
        )

        mock_team_service.require_team_access.assert_awaited_once_with(
            sample_user_id, sample_team_id, min_role=TeamRole.member
        )

    async def test_403_for_guest(
        self,
        service,
        mock_team_service,
        mock_project_repository,
        sample_user_id,
        sample_team_id,
        project_id,
        project_obj,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_project_repository.get = AsyncMock(return_value=project_obj)
        mock_team_service.require_team_access = AsyncMock(
            side_effect=ForbiddenError(detail="guest cannot write")
        )

        with pytest.raises(ForbiddenError):
            await service.update(
                project_id,
                ProjectUpdate(name="X"),
                user_id=sample_user_id,
            )

        mock_project_repository.update.assert_not_awaited()

    async def test_update_validates_lead(
        self,
        service,
        mock_team_service,
        mock_project_repository,
        sample_user_id,
        sample_team_id,
        project_id,
        project_obj,
        lead_id,
        membership_obj,
    ):
        """Updating with a new lead validates they are a team member."""
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_project_repository.get = AsyncMock(return_value=project_obj)
        mock_team_service.get_membership = AsyncMock(return_value=membership_obj)
        mock_project_repository.update = AsyncMock(return_value=project_obj)

        await service.update(
            project_id,
            ProjectUpdate(lead_id=lead_id),
            user_id=sample_user_id,
        )

        mock_team_service.get_membership.assert_awaited_once_with(
            lead_id, sample_team_id
        )

    async def test_update_rejects_non_member_lead(
        self,
        service,
        mock_team_service,
        mock_project_repository,
        sample_user_id,
        sample_team_id,
        project_id,
        project_obj,
        lead_id,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_project_repository.get = AsyncMock(return_value=project_obj)
        mock_team_service.get_membership = AsyncMock(return_value=None)

        with pytest.raises(NotFoundError):
            await service.update(
                project_id,
                ProjectUpdate(lead_id=lead_id),
                user_id=sample_user_id,
            )

        mock_project_repository.update.assert_not_awaited()

    async def test_update_status_changeable(
        self,
        service,
        mock_team_service,
        mock_project_repository,
        sample_user_id,
        sample_team_id,
        project_id,
        project_obj,
    ):
        """Status can be changed to a terminal value (e.g. completed)."""
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_project_repository.get = AsyncMock(return_value=project_obj)
        mock_project_repository.update = AsyncMock(return_value=project_obj)

        await service.update(
            project_id,
            ProjectUpdate(status=ProjectStatus.completed),
            user_id=sample_user_id,
        )

        args, _kwargs = mock_project_repository.update.call_args
        assert args[1].status == ProjectStatus.completed


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


class TestDelete:
    async def test_delete_member_enforced(
        self,
        service,
        mock_team_service,
        mock_project_repository,
        sample_user_id,
        sample_team_id,
        project_id,
        project_obj,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_project_repository.get = AsyncMock(return_value=project_obj)
        mock_project_repository.delete = AsyncMock(return_value=None)

        await service.delete(project_id, user_id=sample_user_id)

        mock_project_repository.delete.assert_awaited_once_with(project_id)

    async def test_404_for_other_team_project(
        self,
        service,
        mock_team_service,
        mock_project_repository,
        sample_user_id,
        other_team_id,
        project_id,
        project_obj,
    ):
        project_obj.team_id = other_team_id
        mock_team_service.get_team_ids_for_user = AsyncMock(return_value=[])
        mock_project_repository.get = AsyncMock(return_value=project_obj)

        with pytest.raises(NotFoundError):
            await service.delete(project_id, user_id=sample_user_id)
