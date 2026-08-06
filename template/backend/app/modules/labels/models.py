"""Label model + IssueLabel association table.

A Label is a team-scoped tag (name + color) that can be attached to issues.
``issue_label`` is the many-to-many association between issues and labels.

NOTE on coordination (m1-issue-backend): the ``issue`` table is created by the
``issues`` module, which does not exist yet. ``issue_label.issue_id`` is declared
as a plain column here (no DB FK constraint) so this module's migration can run
before the ``issue`` table exists. When m1-issue-backend adds the Issue model it
MUST:
  1. add ``ForeignKey("issue.id", ondelete="CASCADE")`` to this ``issue_id``
     column (so the ORM relationship/secondary join resolves), AND
  2. add the corresponding ``issue_label_issue_id_issue_fkey`` constraint in its
     Alembic migration (``op.create_foreign_key(...)``) AFTER creating the
     ``issue`` table.
"""

import uuid

from sqlalchemy import Column, ForeignKey, String, Table, UniqueConstraint, Uuid
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


# Many-to-many association between Issue and Label. See module NOTE above.
issue_label = Table(
    "issue_label",
    Base.metadata,
    Column("issue_id", Uuid, primary_key=True),
    Column(
        "label_id",
        ForeignKey("label.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
