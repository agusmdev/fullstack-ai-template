"""Tests for TeamService."""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.teams.models import TeamRole
from app.modules.teams.schemas import TeamCreate, TeamUpdate
from app.modules.teams.service import TeamService, _derive_key_from_name
from app.repositories.exceptions import NotFoundError


@pytest.fixture
def sample_user_id():
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def sample_team_id():
    return uuid.UUID("99999999-9999-9999-9999-999999999999")


@pytest.fixture
def sample_team(sample_team_id, sample_user_id):
    return SimpleNamespace(
        id=sample_team_id,
        name="Engineering",
        key="ENG",
        issue_sequence=0,
    )


@pytest.fixture
def sample_membership(sample_user_id, sample_team_id):
    return SimpleNamespace(
        id=uuid.uuid4(),
        user_id=sample_user_id,
        team_id=sample_team_id,
        role=TeamRole.admin,
    )


@pytest.fixture
def service(mock_team_repository, mock_team_membership_repository):
    return TeamService(
        repo=mock_team_repository, membership_repo=mock_team_membership_repository
    )


class TestDeriveKeyFromName:
    def test_simple_name(self):
        assert _derive_key_from_name("Engineering") == "ENGI"

    def test_short_name_padded(self):
        assert _derive_key_from_name("Jo") == "JO"

    def test_name_with_spaces_and_special_chars(self):
        assert _derive_key_from_name("Acme Corp!") == "ACME"

    def test_empty_name(self):
        assert _derive_key_from_name("") == "XX"


class TestGetTeamIdsForUser:
    async def test_returns_team_ids_from_memberships(
        self, service, mock_team_membership_repository, sample_user_id
    ):
        team_a = uuid.uuid4()
        team_b = uuid.uuid4()
        mock_team_membership_repository.get_all = AsyncMock(
            return_value=[
                SimpleNamespace(team_id=team_a),
                SimpleNamespace(team_id=team_b),
            ]
        )

        result = await service.get_team_ids_for_user(sample_user_id)

        assert result == [team_a, team_b]

    async def test_returns_empty_when_no_memberships(
        self, service, mock_team_membership_repository, sample_user_id
    ):
        mock_team_membership_repository.get_all = AsyncMock(return_value=[])

        result = await service.get_team_ids_for_user(sample_user_id)

        assert result == []


class TestGetTeamsForUser:
    async def test_returns_team_objects(
        self,
        service,
        mock_team_repository,
        mock_team_membership_repository,
        sample_user_id,
        sample_team,
        sample_team_id,
    ):
        mock_team_membership_repository.get_all = AsyncMock(
            return_value=[SimpleNamespace(team_id=sample_team_id)]
        )
        mock_team_repository.get_all = AsyncMock(return_value=[sample_team])

        result = await service.get_teams_for_user(sample_user_id)

        assert result == [sample_team]

    async def test_returns_empty_when_no_teams(
        self, service, mock_team_membership_repository, sample_user_id
    ):
        mock_team_membership_repository.get_all = AsyncMock(return_value=[])

        result = await service.get_teams_for_user(sample_user_id)

        assert result == []


class TestCreateDefaultTeamForUser:
    async def test_creates_team_and_admin_membership(
        self,
        service,
        mock_team_repository,
        mock_team_membership_repository,
        sample_user_id,
        sample_team,
    ):
        mock_team_repository.get_all = AsyncMock(return_value=[])  # no key collisions
        mock_team_repository.create = AsyncMock(return_value=sample_team)

        result = await service.create_default_team_for_user(sample_user_id, "New User")

        assert result == sample_team
        # Team was created with a generated key
        mock_team_repository.create.assert_awaited_once()
        create_arg = mock_team_repository.create.await_args.args[0]
        assert create_arg.key == "NEWU"
        # Admin membership was created
        mock_team_membership_repository.create.assert_awaited_once()
        membership_arg = mock_team_membership_repository.create.await_args.args[0]
        assert membership_arg.user_id == sample_user_id
        assert membership_arg.team_id == sample_team.id
        assert membership_arg.role == TeamRole.admin

    async def test_generates_unique_key_on_collision(
        self,
        service,
        mock_team_repository,
        mock_team_membership_repository,
        sample_user_id,
        sample_team,
    ):
        # Simulate existing "NEWU" key
        mock_team_repository.get_all = AsyncMock(return_value=["NEWU"])
        mock_team_repository.create = AsyncMock(return_value=sample_team)

        await service.create_default_team_for_user(sample_user_id, "New User")

        create_arg = mock_team_repository.create.await_args.args[0]
        assert create_arg.key == "NEWU2"


class TestCreateTeam:
    async def test_creates_team_and_admin_membership(
        self,
        service,
        mock_team_repository,
        mock_team_membership_repository,
        sample_user_id,
        sample_team,
    ):
        mock_team_repository.create = AsyncMock(return_value=sample_team)

        create_data = TeamCreate(name="My Team", key="MY")
        result = await service.create(create_data, user_id=sample_user_id)

        assert result == sample_team
        mock_team_repository.create.assert_awaited_once_with(create_data)
        mock_team_membership_repository.create.assert_awaited_once()
        membership_arg = mock_team_membership_repository.create.await_args.args[0]
        assert membership_arg.user_id == sample_user_id
        assert membership_arg.role == TeamRole.admin


class TestGetById:
    async def test_returns_team_for_member(
        self,
        service,
        mock_team_repository,
        mock_team_membership_repository,
        sample_user_id,
        sample_team,
        sample_team_id,
        sample_membership,
    ):
        mock_team_membership_repository.get_all = AsyncMock(
            return_value=[sample_membership]
        )
        mock_team_repository.get = AsyncMock(return_value=sample_team)

        result = await service.get_by_id(sample_team_id, user_id=sample_user_id)

        assert result == sample_team

    async def test_raises_not_found_for_non_member(
        self,
        service,
        mock_team_repository,
        mock_team_membership_repository,
        sample_user_id,
        sample_team,
        sample_team_id,
    ):
        mock_team_membership_repository.get_all = AsyncMock(return_value=[])
        mock_team_repository.get = AsyncMock(return_value=sample_team)

        with pytest.raises(NotFoundError):
            await service.get_by_id(sample_team_id, user_id=sample_user_id)


class TestGetAllPaginated:
    async def test_scopes_to_user_teams(
        self,
        service,
        mock_team_repository,
        mock_team_membership_repository,
        sample_user_id,
        sample_team_id,
    ):
        from fastapi_pagination import Params

        mock_team_membership_repository.get_all = AsyncMock(
            return_value=[SimpleNamespace(team_id=sample_team_id)]
        )
        mock_team_repository.get_all_paginated = AsyncMock(
            return_value=MagicMock(items=[], total=0, page=1, size=50, pages=0)
        )

        await service.get_all_paginated(Params(), user_id=sample_user_id)

        mock_team_repository.get_all_paginated.assert_awaited_once()


class TestUpdateTeam:
    async def test_update_by_admin_succeeds(
        self,
        service,
        mock_team_repository,
        mock_team_membership_repository,
        sample_user_id,
        sample_team,
        sample_team_id,
        sample_membership,
    ):
        mock_team_membership_repository.get_all = AsyncMock(
            return_value=[sample_membership]
        )
        mock_team_repository.update = AsyncMock(return_value=sample_team)

        result = await service.update(
            sample_team_id, TeamUpdate(name="Updated"), user_id=sample_user_id
        )

        assert result == sample_team
        mock_team_repository.update.assert_awaited_once()

    async def test_update_by_non_member_raises_404(
        self, service, mock_team_membership_repository, sample_user_id, sample_team_id
    ):
        mock_team_membership_repository.get_all = AsyncMock(return_value=[])

        with pytest.raises(NotFoundError):
            await service.update(
                sample_team_id, TeamUpdate(name="X"), user_id=sample_user_id
            )

    async def test_update_by_guest_raises_404(
        self, service, mock_team_membership_repository, sample_user_id, sample_team_id
    ):
        mock_team_membership_repository.get_all = AsyncMock(
            return_value=[
                SimpleNamespace(
                    id=uuid.uuid4(),
                    user_id=sample_user_id,
                    team_id=sample_team_id,
                    role=TeamRole.guest,
                )
            ]
        )

        with pytest.raises(NotFoundError):
            await service.update(
                sample_team_id, TeamUpdate(name="X"), user_id=sample_user_id
            )


class TestDeleteTeam:
    async def test_delete_by_admin_succeeds(
        self,
        service,
        mock_team_repository,
        mock_team_membership_repository,
        sample_user_id,
        sample_team_id,
        sample_membership,
    ):
        mock_team_membership_repository.get_all = AsyncMock(
            return_value=[sample_membership]
        )
        mock_team_repository.delete = AsyncMock(return_value=None)

        await service.delete(sample_team_id, user_id=sample_user_id)

        mock_team_repository.delete.assert_awaited_once_with(sample_team_id)

    async def test_delete_by_non_member_raises_404(
        self, service, mock_team_membership_repository, sample_user_id, sample_team_id
    ):
        mock_team_membership_repository.get_all = AsyncMock(return_value=[])

        with pytest.raises(NotFoundError):
            await service.delete(sample_team_id, user_id=sample_user_id)
