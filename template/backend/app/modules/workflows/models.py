"""WorkflowState model — the status lifecycle for a team's issues.

A WorkflowState represents a column/status in a team's issue workflow (e.g.
Backlog, Todo, In Progress, Done, Canceled). ``type`` drives behaviour (which
states are terminal, etc.) while ``name`` is the display label. ``position`` is
a float so states can be reordered between existing ones.
"""

import enum
import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import TimestampMixin


class WorkflowStateType(str, enum.Enum):
    """Behavioural type of a workflow state.

    backlog:    triage / not yet planned.
    unstarted:  planned but not in progress (e.g. "Todo").
    started:    actively being worked on (e.g. "In Progress").
    completed:  finished successfully (terminal).
    canceled:   abandoned (terminal).
    """

    backlog = "backlog"
    unstarted = "unstarted"
    started = "started"
    completed = "completed"
    canceled = "canceled"


class WorkflowState(TimestampMixin, Base):
    """A status/state in a team's issue workflow.

    Attributes:
        team_id:  Owning team (FK team.id, CASCADE).
        name:     Display name (unique per team).
        type:     Behavioural type (drives terminal/grouping logic).
        position: Sort order within the team (float for flexible reordering).
        color:    Optional hex color for UI badges.
    """

    __tablename__ = "workflow_state"
    __table_args__ = (
        UniqueConstraint("team_id", "name", name="workflow_state_team_name_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("team.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[WorkflowStateType] = mapped_column(
        SAEnum(WorkflowStateType, name="workflow_state_type"),
    )
    position: Mapped[float] = mapped_column(Float, default=0.0)
    color: Mapped[str | None] = mapped_column(String(32), nullable=True)
