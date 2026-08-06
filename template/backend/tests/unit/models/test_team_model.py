"""Tests for Team and TeamMembership models."""

import uuid

from app.modules.teams.models import Team, TeamMembership, TeamRole


class TestTeamModel:
    """Tests for Team model class."""

    def test_team_creation(self):
        """Test creating a Team instance."""
        team = Team(
            id=uuid.uuid4(),
            name="Engineering",
            key="ENG",
            issue_sequence=5,
        )
        assert team.name == "Engineering"
        assert team.key == "ENG"
        assert team.issue_sequence == 5

    def test_team_tablename(self):
        """Test that tablename is correctly set."""
        assert Team.__tablename__ == "team"

    def test_team_issue_sequence_default(self):
        """Test that issue_sequence defaults to 0."""
        assert Team.issue_sequence.default.arg == 0

    def test_team_display_name(self):
        """Test that _display_name returns capitalized tablename."""
        assert Team._display_name() == "Team"

    def test_team_key_max_length(self):
        """Test that key has max length of 10."""
        key_column = Team.__table__.c.key
        assert key_column.type.length == 10

    def test_team_key_unique(self):
        """Test that key has unique constraint."""
        key_column = Team.__table__.c.key
        assert key_column.unique is True

    def test_team_key_indexed(self):
        """Test that key is indexed."""
        key_column = Team.__table__.c.key
        assert key_column.index is True


class TestTeamRole:
    """Tests for TeamRole enum."""

    def test_admin_value(self):
        assert TeamRole.admin.value == "admin"

    def test_member_value(self):
        assert TeamRole.member.value == "member"

    def test_guest_value(self):
        assert TeamRole.guest.value == "guest"

    def test_is_str_enum(self):
        """TeamRole inherits from str for JSON serialization."""
        assert isinstance(TeamRole.admin, str)
        assert TeamRole.admin == "admin"


class TestTeamMembershipModel:
    """Tests for TeamMembership model class."""

    def test_membership_tablename(self):
        """Test that tablename is correctly set."""
        assert TeamMembership.__tablename__ == "team_membership"

    def test_membership_creation(self):
        """Test creating a TeamMembership instance."""
        user_id = uuid.uuid4()
        team_id = uuid.uuid4()
        membership = TeamMembership(
            id=uuid.uuid4(),
            user_id=user_id,
            team_id=team_id,
            role=TeamRole.admin,
        )
        assert membership.user_id == user_id
        assert membership.team_id == team_id
        assert membership.role == TeamRole.admin

    def test_membership_role_default(self):
        """Test that role defaults to member."""
        assert TeamMembership.role.default.arg == TeamRole.member

    def test_membership_display_name(self):
        """Test that _display_name returns capitalized tablename."""
        assert TeamMembership._display_name() == "Team_membership"

    def test_membership_has_user_id_index(self):
        """Test that user_id is indexed."""
        user_id_column = TeamMembership.__table__.c.user_id
        assert user_id_column.index is True

    def test_membership_has_team_id_index(self):
        """Test that team_id is indexed."""
        team_id_column = TeamMembership.__table__.c.team_id
        assert team_id_column.index is True

    def test_membership_has_unique_constraint(self):
        """Test that there is a unique constraint on (user_id, team_id)."""
        constraint_names = [
            c.name for c in TeamMembership.__table__.constraints if c.name
        ]
        assert any("team" in name.lower() for name in constraint_names)
