"""add comments module

Revision ID: d9ead1664eef
Revises: c8e629dcdb12
Create Date: 2026-08-07 07:47:02.068260

Creates the ``comment`` table — discussion messages on issues
(``issue_id`` → ``issue``, ``author_id`` → ``user``, both CASCADE). The author is
eager-joined by the repository so responses can render the author name without
an N+1 (VAL-COMMENTS-004). Comments are team-scoped transitively via their
issue's team; the service layer authorizes via that team membership.

Pre-existing user-table drift (email_verified_at TIMESTAMP vs DateTime,
user_email unique index) and missing project timestamp indexes are
intentionally NOT included — see AGENTS.md "Known Pre-Existing Issues".
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d9ead1664eef"
down_revision: str | None = "c8e629dcdb12"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "comment",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("issue_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["user.id"],
            name=op.f("comment_author_id_user_fkey"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["issue_id"],
            ["issue.id"],
            name=op.f("comment_issue_id_issue_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("comment_pkey")),
    )
    op.create_index(
        op.f("comment_author_id_idx"), "comment", ["author_id"], unique=False
    )
    op.create_index(
        op.f("comment_created_at_idx"), "comment", ["created_at"], unique=False
    )
    op.create_index(op.f("comment_issue_id_idx"), "comment", ["issue_id"], unique=False)
    op.create_index(
        op.f("comment_updated_at_idx"), "comment", ["updated_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("comment_updated_at_idx"), table_name="comment")
    op.drop_index(op.f("comment_issue_id_idx"), table_name="comment")
    op.drop_index(op.f("comment_created_at_idx"), table_name="comment")
    op.drop_index(op.f("comment_author_id_idx"), table_name="comment")
    op.drop_table("comment")
