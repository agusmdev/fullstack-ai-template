"""Tests for Team and TeamMembership schemas."""

import uuid

import pytest
from pydantic import ValidationError

from app.modules.teams.models import TeamRole
from app.modules.teams.schemas import (
    TeamBase,
    TeamCreate,
    TeamMembershipCreate,
    TeamMembershipResponse,
    TeamResponse,
    TeamUpdate,
)


class TestTeamBase:
    """Tests for TeamBase schema."""

    def test_valid_team(self):
        team = TeamBase(name="Engineering", key="ENG")
        assert team.name == "Engineering"
        assert team.key == "ENG"

    def test_name_required(self):
        with pytest.raises(ValidationError) as exc_info:
            TeamBase(key="ENG")
        assert "name" in str(exc_info.value)

    def test_key_required(self):
        with pytest.raises(ValidationError) as exc_info:
            TeamBase(name="Engineering")
        assert "key" in str(exc_info.value)

    def test_name_min_length(self):
        with pytest.raises(ValidationError):
            TeamBase(name="", key="ENG")

    def test_key_min_length(self):
        with pytest.raises(ValidationError):
            TeamBase(name="Engineering", key="X")

    def test_key_max_length(self):
        with pytest.raises(ValidationError):
            TeamBase(name="Engineering", key="X" * 11)


class TestTeamCreate:
    def test_inherits_from_team_base(self):
        assert issubclass(TeamCreate, TeamBase)

    def test_create_team(self):
        team = TeamCreate(name="New Team", key="NEW")
        assert team.name == "New Team"


class TestTeamUpdate:
    def test_all_fields_optional(self):
        update = TeamUpdate()
        assert update.name is None
        assert update.key is None

    def test_partial_update(self):
        update = TeamUpdate(name="Updated")
        assert update.name == "Updated"
        assert update.key is None


class TestTeamResponse:
    def test_includes_id_and_issue_sequence(self):
        team_id = uuid.uuid4()
        team = TeamResponse(id=team_id, name="Test", key="TEST", issue_sequence=3)
        assert team.id == team_id
        assert team.issue_sequence == 3

    def test_issue_sequence_defaults_to_zero(self):
        team = TeamResponse(id=uuid.uuid4(), name="Test", key="TEST")
        assert team.issue_sequence == 0

    def test_from_attributes_mode(self):
        assert TeamResponse.model_config.get("from_attributes") is True


class TestTeamMembershipCreate:
    def test_create_membership(self):
        user_id = uuid.uuid4()
        team_id = uuid.uuid4()
        membership = TeamMembershipCreate(
            user_id=user_id, team_id=team_id, role=TeamRole.admin
        )
        assert membership.user_id == user_id
        assert membership.team_id == team_id
        assert membership.role == TeamRole.admin

    def test_role_defaults_to_member(self):
        membership = TeamMembershipCreate(user_id=uuid.uuid4(), team_id=uuid.uuid4())
        assert membership.role == TeamRole.member


class TestTeamMembershipResponse:
    def test_includes_id(self):
        membership = TeamMembershipResponse(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            team_id=uuid.uuid4(),
            role=TeamRole.guest,
        )
        assert membership.role == TeamRole.guest

    def test_from_attributes_mode(self):
        assert TeamMembershipResponse.model_config.get("from_attributes") is True
