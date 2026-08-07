"""Team and TeamMembership schemas — request and response models."""

import uuid

from pydantic import BaseModel, Field

from app.core.optional_model import partial_model
from app.database.mixins import OrmBaseModel
from app.modules.teams.models import TeamRole


class TeamBase(BaseModel):
    """Common team fields."""

    name: str = Field(..., min_length=1, max_length=255)
    key: str = Field(..., min_length=2, max_length=10)


class TeamCreate(TeamBase):
    """Schema for creating a new team."""

    pass


@partial_model
class TeamUpdate(TeamBase):
    """Schema for updating a team (all fields optional)."""

    pass


class TeamResponse(TeamBase, OrmBaseModel):
    """Team response including id and issue counter."""

    id: uuid.UUID
    issue_sequence: int = 0


class TeamListItemResponse(TeamResponse):
    """Team list item enriched with the requesting user's role in the team.

    The frontend uses ``my_role`` to gate role-based UI (e.g. disable the
    "New issue" button for guests, hide admin-only actions from members)
    without a second round-trip (VAL-CROSS-025).
    """

    my_role: TeamRole


class TeamMembershipBase(BaseModel):
    """Common membership fields."""

    user_id: uuid.UUID
    team_id: uuid.UUID
    role: TeamRole = TeamRole.member


class TeamMembershipCreate(TeamMembershipBase):
    """Schema for creating a team membership."""

    pass


class TeamMembershipResponse(TeamMembershipBase, OrmBaseModel):
    """Team membership response."""

    id: uuid.UUID
