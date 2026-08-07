"""View model — a saved issue view (filters + group_by + order_by).

A ``View`` captures a snapshot of the Issues/Board view configuration: the
active filters (JSONB), the grouping mode, and the sort order. It is scoped to a
team (so it shows in the team sidebar) and owned by the user who created it.

Applying a saved view navigates to the issues/board route with the stored
configuration serialized as URL search params. Dirty (locally-modified) changes
never overwrite the stored configuration — the view is only updated by an
explicit re-save (VAL-VIEWS-006).
"""

import uuid
from typing import Any

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import TimestampMixin


class View(TimestampMixin, Base):
    """A saved issue view (filters + group_by + order_by).

    Attributes:
        owner_id:  The user who created the view (FK user.id, SET NULL).
        team_id:   Owning team (FK team.id, CASCADE) — the view shows in this
                   team's sidebar and is listable/scoped by it.
        name:      Human-readable name (required, unique per team+owner).
        filters:   JSONB snapshot of the active filters
                   (``q``/``status_id``/``priority``/``assignee``/``label_id``).
        group_by:  Grouping mode (e.g. ``"status"``); nullable for "no grouping".
        order_by:  Sort preset key (e.g. ``"newest"``); nullable for default.
        description: Optional free-text note.
    """

    __tablename__ = "view"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("team.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    filters: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    group_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    order_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
