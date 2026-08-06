"""Tests for WorkflowStateService (team-scoped, admin-write)."""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi_pagination import Params

from app.modules.teams.models import TeamRole
from app.modules.workflows.models import WorkflowStateType
from app.modules.workflows.schemas import WorkflowStateCreate, WorkflowStateUpdate
from app.modules.workflows.service import WorkflowStateService
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
def state_id():
    return uuid.UUID("44444444-4444-4444-4444-444444444444")


@pytest.fixture
def state_obj(state_id, sample_team_id):
    return SimpleNamespace(
        id=state_id,
        team_id=sample_team_id,
        name="In Progress",
        type=WorkflowStateType.started,
        position=2.0,
        color="#f2c94c",
    )


@pytest.fixture
def service(mock_workflow_state_repository, mock_team_service):
    return WorkflowStateService(
        repo=mock_workflow_state_repository, team_service=mock_team_service
    )


class TestGetAllPaginated:
    async def test_scopes_to_user_teams(
        self,
        service,
        mock_workflow_state_repository,
        mock_team_service,
        sample_user_id,
        sample_team_id,
        state_obj,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_workflow_state_repository.get_all_paginated = AsyncMock(
            return_value=SimpleNamespace(
                items=[state_obj], total=1, page=1, size=50, pages=1
            )
        )

        result = await service.get_all_paginated(Params(), user_id=sample_user_id)

        assert result.total == 1
        mock_workflow_state_repository.get_all_paginated.assert_awaited_once()

    async def test_team_id_filter_restricts_to_member_team(
        self,
        service,
        mock_team_service,
        sample_user_id,
        sample_team_id,
        state_obj,
        mock_workflow_state_repository,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_workflow_state_repository.get_all_paginated = AsyncMock(
            return_value=SimpleNamespace(
                items=[state_obj], total=1, page=1, size=50, pages=1
            )
        )

        await service.get_all_paginated(
            Params(), user_id=sample_user_id, team_id=sample_team_id
        )

        mock_workflow_state_repository.get_all_paginated.assert_awaited_once()

    async def test_team_id_filter_404_for_non_member_team(
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
    async def test_returns_state_for_member(
        self,
        service,
        mock_workflow_state_repository,
        mock_team_service,
        sample_user_id,
        sample_team_id,
        state_id,
        state_obj,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_workflow_state_repository.get = AsyncMock(return_value=state_obj)

        result = await service.get_by_id(state_id, user_id=sample_user_id)

        assert result == state_obj

    async def test_404_for_other_team_state(
        self,
        service,
        mock_workflow_state_repository,
        mock_team_service,
        sample_user_id,
        other_team_id,
        state_id,
        state_obj,
    ):
        # state belongs to other_team; user is not a member
        state_obj.team_id = other_team_id
        mock_team_service.get_team_ids_for_user = AsyncMock(return_value=[])
        mock_workflow_state_repository.get = AsyncMock(return_value=state_obj)

        with pytest.raises(NotFoundError):
            await service.get_by_id(state_id, user_id=sample_user_id)


class TestCreate:
    async def test_requires_admin_role(
        self,
        service,
        mock_team_service,
        mock_workflow_state_repository,
        sample_user_id,
        sample_team_id,
        state_obj,
    ):
        mock_workflow_state_repository.create = AsyncMock(return_value=state_obj)

        await service.create(
            WorkflowStateCreate(
                team_id=sample_team_id,
                name="Triage",
                type=WorkflowStateType.backlog,
                position=0.5,
            ),
            user_id=sample_user_id,
        )

        mock_team_service.require_team_access.assert_awaited_once_with(
            sample_user_id, sample_team_id, min_role=TeamRole.admin
        )
        mock_workflow_state_repository.create.assert_awaited_once()


class TestUpdate:
    async def test_update_admin_enforced(
        self,
        service,
        mock_team_service,
        mock_workflow_state_repository,
        sample_user_id,
        sample_team_id,
        state_id,
        state_obj,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_workflow_state_repository.get = AsyncMock(return_value=state_obj)
        mock_workflow_state_repository.update = AsyncMock(return_value=state_obj)

        await service.update(
            state_id, WorkflowStateUpdate(name="Renamed"), user_id=sample_user_id
        )

        mock_team_service.require_team_access.assert_awaited_once_with(
            sample_user_id, sample_team_id, min_role=TeamRole.admin
        )


class TestDelete:
    async def test_delete_admin_enforced(
        self,
        service,
        mock_team_service,
        mock_workflow_state_repository,
        sample_user_id,
        sample_team_id,
        state_id,
        state_obj,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_workflow_state_repository.get = AsyncMock(return_value=state_obj)
        mock_workflow_state_repository.delete = AsyncMock(return_value=None)

        await service.delete(state_id, user_id=sample_user_id)

        mock_workflow_state_repository.delete.assert_awaited_once_with(state_id)
