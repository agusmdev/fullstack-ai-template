"""Label model + IssueLabel association table.

A Label is a team-scoped tag (name + color) that can be attached to issues.
``issue_label`` is the many-to-many association between issues and labels.

Both FKs (``issue.id`` and ``label.id``) are wired with ``ondelete="CASCADE"``.
The ``issue_label_issue_id_issue_fkey`` constraint is created in the issues
module's migration (``op.create_foreign_key``) after the ``issue`` table exists.
"""

import uuid

from sqlalchemy import Column, ForeignKey, String, Table, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import TimestampMixin


class Label(TimestampMixin, Base):
    """A team-scoped label/tag that can be attached to issues.

    Attributes:
        team_id: Owning team (FK team.id, CASCADE).
        name:    Label text (unique per team).
        color:   Optional hex color for UI badges.
    """

    __tablename__ = "label"
    __table_args__ = (UniqueConstraint("team_id", "name", name="label_team_name_key"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("team.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    color: Mapped[str | None] = mapped_column(String(32), nullable=True)


# Many-to-many association between Issue and Label.
# The issue_id FK is now wired (the Issue table exists in the issues module).
issue_label = Table(
    "issue_label",
    Base.metadata,
    Column(
        "issue_id",
        ForeignKey("issue.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "label_id",
        ForeignKey("label.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
