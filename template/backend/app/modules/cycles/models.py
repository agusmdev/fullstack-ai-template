"""Cycle model — a team-scoped time-boxed sprint.

A Cycle is a fixed date window (``starts_at`` → ``ends_at``) used to group
issues into a sprint-like iteration. Issues link to a cycle via
``Issue.cycle_id`` (M2); an issue belongs to at most one cycle at a time
(reassigning moves it). ``completed_at`` marks when the cycle was finished
(nullable while the cycle is active or upcoming).
"""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import TimestampMixin


class Cycle(TimestampMixin, Base):
    """A team-scoped time-boxed sprint.

    Attributes:
        team_id:      Owning team (FK team.id, CASCADE).
        name:         Cycle name (unique per team).
        starts_at:    Cycle start date (inclusive).
        ends_at:      Cycle end date (inclusive); must be after ``starts_at``.
        completed_at: When the cycle was completed (nullable while active/upcoming).
    """

    __tablename__ = "cycle"
    __table_args__ = (UniqueConstraint("team_id", "name", name="cycle_team_name_key"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("team.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    starts_at: Mapped[date] = mapped_column(Date, nullable=False)
    ends_at: Mapped[date] = mapped_column(Date, nullable=False)
    completed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
