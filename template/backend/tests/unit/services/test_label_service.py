"""Tests for LabelService (team-scoped, member-write)."""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi_pagination import Params

from app.modules.labels.models import Label
from app.modules.labels.schemas import LabelCreate, LabelUpdate
from app.modules.labels.service import LabelService
from app.modules.teams.models import TeamRole
from app.repositories.exceptions import NotFoundError


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
def label_id():
    return uuid.UUID("55555555-5555-5555-5555-555555555555")


@pytest.fixture
def label_obj(label_id, sample_team_id):
    return SimpleNamespace(
        id=label_id,
        team_id=sample_team_id,
        name="Bug",
        color="#eb5757",
    )


@pytest.fixture
def service(mock_label_repository, mock_team_service):
    return LabelService(repo=mock_label_repository, team_service=mock_team_service)


class TestGetAllPaginated:
    async def test_scopes_to_user_teams(
        self,
        service,
        mock_label_repository,
        mock_team_service,
        sample_user_id,
        sample_team_id,
        label_obj,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_label_repository.get_all_paginated = AsyncMock(
            return_value=SimpleNamespace(
                items=[label_obj], total=1, page=1, size=50, pages=1
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
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )

        with pytest.raises(NotFoundError):
            await service.get_all_paginated(
                Params(), user_id=sample_user_id, team_id=other_team_id
            )


class TestGetById:
    async def test_returns_label_for_member(
        self,
        service,
        mock_label_repository,
        mock_team_service,
        sample_user_id,
        sample_team_id,
        label_id,
        label_obj,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_label_repository.get = AsyncMock(return_value=label_obj)

        result = await service.get_by_id(label_id, user_id=sample_user_id)

        assert result == label_obj

    async def test_404_for_other_team_label(
        self,
        service,
        mock_label_repository,
        mock_team_service,
        sample_user_id,
        other_team_id,
        label_id,
        label_obj,
    ):
        label_obj.team_id = other_team_id
        mock_team_service.get_team_ids_for_user = AsyncMock(return_value=[])
        mock_label_repository.get = AsyncMock(return_value=label_obj)

        with pytest.raises(NotFoundError):
            await service.get_by_id(label_id, user_id=sample_user_id)


class TestCreate:
    async def test_requires_member_role(
        self,
        service,
        mock_team_service,
        mock_label_repository,
        sample_user_id,
        sample_team_id,
        label_obj,
    ):
        mock_label_repository.create = AsyncMock(return_value=label_obj)

        await service.create(
            LabelCreate(team_id=sample_team_id, name="Bug", color="#eb5757"),
            user_id=sample_user_id,
        )

        mock_team_service.require_team_access.assert_awaited_once_with(
            sample_user_id, sample_team_id, min_role=TeamRole.member
        )


class TestUpdate:
    async def test_update_member_enforced(
        self,
        service,
        mock_team_service,
        mock_label_repository,
        sample_user_id,
        sample_team_id,
        label_id,
        label_obj,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_label_repository.get = AsyncMock(return_value=label_obj)
        mock_label_repository.update = AsyncMock(return_value=label_obj)

        await service.update(
            label_id, LabelUpdate(name="Feature"), user_id=sample_user_id
        )

        mock_team_service.require_team_access.assert_awaited_once_with(
            sample_user_id, sample_team_id, min_role=TeamRole.member
        )


class TestDelete:
    async def test_delete_member_enforced(
        self,
        service,
        mock_team_service,
        mock_label_repository,
        sample_user_id,
        sample_team_id,
        label_id,
        label_obj,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_label_repository.get = AsyncMock(return_value=label_obj)
        mock_label_repository.delete = AsyncMock(return_value=None)

        await service.delete(label_id, user_id=sample_user_id)

        mock_label_repository.delete.assert_awaited_once_with(label_id)


class TestIssueLabelModel:
    def test_issue_label_table_registered(self):
        """The association table must be registered on Base.metadata."""
        from app.database.base import Base
        from app.modules.labels.models import issue_label

        assert "issue_label" in Base.metadata.tables
        assert issue_label.name == "issue_label"
        # composite PK
        assert {c.name for c in issue_label.primary_key.columns} == {
            "issue_id",
            "label_id",
        }
        # both FKs now wired (issue FK added by m1-issue-backend)
        fk_targets = {
            fk.target_fullname for c in issue_label.columns for fk in c.foreign_keys
        }
        assert "label.id" in fk_targets
        assert "issue.id" in fk_targets

    def test_label_model_fields(self):
        cols = {c.name for c in Label.__table__.columns}
        assert {"id", "team_id", "name", "color", "created_at", "updated_at"} <= cols
