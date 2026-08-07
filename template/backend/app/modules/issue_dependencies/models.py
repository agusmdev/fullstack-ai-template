"""IssueDependency model — a 'blocks' relationship between two issues.

A dependency records that one issue (the **blocker**) blocks another (the
**blocked**). The relationship is directional: ``A blocks B`` means A must be
done before B can proceed. Both issues must belong to the same team (enforced in
the service layer); the relationship is therefore inherently team-scoped.

A compound unique constraint on ``(blocker_id, blocked_id)`` prevents duplicate
links between the same pair (VAL-DEPS-001).
"""

import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.mixins import TimestampMixin


class IssueDependency(TimestampMixin, Base):
    """A 'blocks' dependency between two issues.

    Attributes:
        blocker_id:  The issue that blocks (FK issue.id, CASCADE). "A blocks B"
                     → A is the blocker.
        blocked_id:  The issue that is blocked (FK issue.id, CASCADE). "A blocks
                     B" → B is the blocked.
        relation:    The relation type (always ``"blocks"`` for now; stored for
                     forward compatibility). Defaults to ``"blocks"``.
    """

    __tablename__ = "issue_dependency"
    __table_args__ = (
        UniqueConstraint("blocker_id", "blocked_id", name="issue_dependency_pair_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    blocker_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("issue.id", ondelete="CASCADE"), index=True
    )
    blocked_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("issue.id", ondelete="CASCADE"), index=True
    )
    relation: Mapped[str] = mapped_column(
        String(32), default="blocks", server_default="blocks"
    )

    # Eager-loaded related issues so list/detail responses can render reciprocal
    # display (blocker "blocking X", blocked "blocked by Y") without N+1
    # (VAL-DEPS-002). ``foreign_keys`` is required because both FKs target the
    # same table.
    blocker = relationship(
        "Issue", foreign_keys=[blocker_id], lazy="joined", passive_deletes=True
    )
    blocked = relationship(
        "Issue", foreign_keys=[blocked_id], lazy="joined", passive_deletes=True
    )
