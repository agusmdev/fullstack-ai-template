"""Comment model — a discussion message on an issue.

A Comment belongs to exactly one Issue and has a single Author (the user who
wrote it). Comments are team-scoped transitively: their issue belongs to a
team, so the service layer authorizes via the issue's team membership. The
author is eager-loaded so responses can render the author name without an N+1
(VAL-COMMENTS-004).
"""

import uuid

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.mixins import TimestampMixin


class Comment(TimestampMixin, Base):
    """A discussion message on an issue.

    Attributes:
        issue_id:  The issue this comment belongs to (FK issue.id, CASCADE).
        author_id: The user who wrote the comment (FK user.id, CASCADE).
        body:      The comment text (required, non-empty — enforced in the
                   service layer; whitespace-only is rejected).
    """

    __tablename__ = "comment"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    issue_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("issue.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), index=True
    )
    body: Mapped[str] = mapped_column(Text)

    # Eager-load the author (joined) so list/detail responses can render the
    # author name/email without an N+1 or a lazy-load outside an async context
    # (VAL-COMMENTS-004).
    author = relationship(
        "User", foreign_keys=[author_id], lazy="joined", passive_deletes=True
    )
