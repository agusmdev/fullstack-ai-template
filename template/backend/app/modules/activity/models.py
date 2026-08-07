"""Activity model — an auto-generated, read-only audit entry for an issue.

An :class:`Activity` row records a single mutation on an issue (status change,
assignee change, priority change, title rename, label added/removed). Entries
are **auto-generated** by ``IssueService`` on every qualifying mutation and are
**read-only** — there is no create/update/delete endpoint exposed to clients
(VAL-ACTIVITY-009). The actor (the user who performed the action) is
eager-loaded so the activity feed can render the actor name without an N+1
(VAL-ACTIVITY-007).

Activity is team-scoped transitively: its issue belongs to a team, so the
service layer authorizes reads via that team membership.
"""

import uuid
from typing import Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.mixins import TimestampMixin

# ---------------------------------------------------------------------------
# Activity type vocabulary (the ``type`` column values).
# ---------------------------------------------------------------------------
# These constants are the canonical ``type`` values stored on every Activity
# row and rendered by the SPA. They are intentionally plain strings (not an
# enum column) so the schema stays open to future activity kinds without a
# migration, while still being centrally defined for type-safety on the write
# side (``IssueService``) and readability on the SPA side.
STATUS_CHANGE = "status_change"
ASSIGNEE_CHANGE = "assignee_change"
PRIORITY_CHANGE = "priority_change"
TITLE_RENAME = "title_rename"
LABEL_ADDED = "label_added"
LABEL_REMOVED = "label_removed"


class Activity(TimestampMixin, Base):
    """An auto-generated, read-only activity entry for an issue.

    Attributes:
        issue_id:  The issue this entry describes (FK issue.id, CASCADE).
        actor_id:  The user who performed the action (FK user.id, CASCADE).
        type:      The activity kind — one of the module constants above.
        payload:   Structured, JSON-serializable detail for the kind, e.g.
                   ``{"from": "Backlog", "to": "In Progress"}`` for a status
                   change. Stored as JSONB so the feed can render rich context
                   without extra fetches.
    """

    __tablename__ = "activity"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    issue_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("issue.id", ondelete="CASCADE"), index=True
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )

    # Eager-load the actor (joined) so list/detail responses can render the
    # actor name/email without an N+1 or a lazy-load outside an async context
    # (VAL-ACTIVITY-007).
    actor = relationship(
        "User", foreign_keys=[actor_id], lazy="joined", passive_deletes=True
    )
