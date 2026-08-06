"""Issue model — the core entity (hub of the data model).

An Issue is a team-scoped work item with an auto-generated identifier
(``TEAM-NN``), title, description, status (workflow state), priority,
assignee, creator, optional project/cycle links (M2), optional parent
(sub-issue, M3), sort order, estimate, and due date.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.mixins import TimestampMixin
from app.modules.labels.models import Label, issue_label


class Issue(TimestampMixin, Base):
    """A work item — the central entity in the Linear data model.

    Attributes:
        team_id:      Owning team (FK team.id, CASCADE).
        identifier:   Auto-generated ``TEAM-NN`` (unique per team).
        title:        Short summary (required, 1–512 chars).
        description:  Optional rich-text/markdown body.
        status_id:    Current workflow state (FK workflow_state.id, CASCADE).
        priority:     0=Urgent … 4=No priority (default 4).
        assignee_id:  Assigned user (FK user.id, nullable, SET NULL).
        creator_id:   User who created the issue (FK user.id, CASCADE).
        project_id:   Optional project link (M2 — plain UUID, no FK yet).
        cycle_id:     Optional cycle link (M2 — plain UUID, no FK yet).
        parent_id:    Self-reference for sub-issues (FK issue.id, SET NULL).
        sort_order:   Float for flexible ordering within a group.
        estimate:     Optional story-point estimate.
        due_date:     Optional due date.
    """

    __tablename__ = "issue"
    __table_args__ = (
        UniqueConstraint("team_id", "identifier", name="issue_team_identifier_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("team.id", ondelete="CASCADE"), index=True
    )
    identifier: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflow_state.id", ondelete="CASCADE"), index=True
    )
    priority: Mapped[int] = mapped_column(Integer, default=4, server_default="4")

    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), index=True
    )

    # M2 links. project_id now has a FK to the project table (added by
    # m2-projects); cycle_id remains a plain UUID until m2-cycles wires its FK.
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("project.id", ondelete="SET NULL"), nullable=True, index=True
    )
    cycle_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)

    # M3 self-reference for sub-issues.
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("issue.id", ondelete="SET NULL"), nullable=True, index=True
    )

    sort_order: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0")
    estimate: Mapped[float | None] = mapped_column(Float, nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Eager-loaded labels via selectin strategy (avoids N+1 on list/board queries).
    labels: Mapped[list[Label]] = relationship(
        secondary=issue_label, lazy="selectin", cascade="all, delete"
    )
