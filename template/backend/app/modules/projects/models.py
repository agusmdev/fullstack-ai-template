"""Project model — a team-scoped collection of related issues.

A Project groups issues that roll up to a shared initiative (e.g. a feature,
migration, or quarter goal). It carries an editable lifecycle ``status``
(defaulting to a non-terminal value), an optional ``lead_id`` (a team member),
and an optional ``target_date``.

Issues are linked to a project via ``Issue.project_id`` (M2). The foreign-key
constraint from ``issue.project_id → project.id`` is wired in the projects
migration.
"""

import enum
import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import TimestampMixin


class ProjectStatus(str, enum.Enum):
    """Lifecycle status of a project.

    ``planned`` and ``started`` are non-terminal (active) states;
    ``completed`` and ``canceled`` are terminal.
    """

    planned = "planned"
    started = "started"
    completed = "completed"
    canceled = "canceled"


class Project(TimestampMixin, Base):
    """A team-scoped project grouping related issues.

    Attributes:
        team_id:     Owning team (FK team.id, CASCADE).
        name:        Project name (unique per team).
        status:      Lifecycle status (defaults to ``planned`` — non-terminal).
        lead_id:     Optional project lead (FK user.id, SET NULL).
        target_date: Optional target completion date.
        description: Optional rich-text/markdown body.
    """

    __tablename__ = "project"
    __table_args__ = (
        UniqueConstraint("team_id", "name", name="project_team_name_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("team.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[ProjectStatus] = mapped_column(
        SAEnum(ProjectStatus, name="project_status"),
        default=ProjectStatus.planned,
        server_default=ProjectStatus.planned.value,
    )
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True
    )
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
