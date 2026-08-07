"""Team and TeamMembership models.

A Team is the top-level scoping entity for all Linear domain objects (issues,
projects, cycles, etc.). Team.issue_sequence is a per-team counter used to
generate monotonically increasing issue identifiers (e.g. ``ENG-1``).

TeamMembership links a User to a Team with a role (admin / member / guest) and
is the foundation for team-scoped authorization across all later modules.
"""

import enum
import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import TimestampMixin


class TeamRole(str, enum.Enum):
    """Role of a user within a team.

    admin:  full control — manage team settings, members, workflows.
    member: create/edit issues; cannot manage members or workflows.
    guest:  read-only access.
    """

    admin = "admin"
    member = "member"
    guest = "guest"


class Team(TimestampMixin, Base):
    """A team / workspace that owns all domain entities.

    Attributes:
        name: Human-readable team name.
        key: Short identifier prefix used in issue identifiers (e.g. ``ENG``).
        issue_sequence: Monotonic counter incremented per issue create; starts at 0.
    """

    __tablename__ = "team"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    key: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    issue_sequence: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class TeamMembership(TimestampMixin, Base):
    """Association between a User and a Team with an authorization role."""

    __tablename__ = "team_membership"
    __table_args__ = (
        UniqueConstraint("user_id", "team_id", name="team_membership_user_team_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), index=True
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("team.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[TeamRole] = mapped_column(
        SAEnum(TeamRole, name="team_role"),
        default=TeamRole.member,
        server_default=TeamRole.member.value,
    )
