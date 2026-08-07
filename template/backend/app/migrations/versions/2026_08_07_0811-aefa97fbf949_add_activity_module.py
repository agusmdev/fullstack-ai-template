"""add activity module

Revision ID: aefa97fbf949
Revises: d9ead1664eef
Create Date: 2026-08-07 08:11:25.472084

Creates the ``activity`` table — the auto-generated, read-only activity log for
issues (``issue_id`` → ``issue``, ``actor_id`` → ``user``, both CASCADE). The
actor is eager-joined by the repository so the feed can render the actor name
without an N+1 (VAL-ACTIVITY-007). Entries are written by ``IssueService`` on
qualifying issue mutations; activity is team-scoped transitively via its
issue's team.

Pre-existing drift (project timestamp indexes, user-table email_verified_at
TIMESTAMP vs DateTime, user_email unique index) is intentionally NOT included
— see AGENTS.md "Known Pre-Existing Issues".
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "aefa97fbf949"
down_revision: str | None = "d9ead1664eef"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "activity",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("issue_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["user.id"],
            name=op.f("activity_actor_id_user_fkey"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["issue_id"],
            ["issue.id"],
            name=op.f("activity_issue_id_issue_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("activity_pkey")),
    )
    op.create_index(
        op.f("activity_actor_id_idx"), "activity", ["actor_id"], unique=False
    )
    op.create_index(
        op.f("activity_created_at_idx"), "activity", ["created_at"], unique=False
    )
    op.create_index(
        op.f("activity_issue_id_idx"), "activity", ["issue_id"], unique=False
    )
    op.create_index(
        op.f("activity_updated_at_idx"), "activity", ["updated_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("activity_updated_at_idx"), table_name="activity")
    op.drop_index(op.f("activity_issue_id_idx"), table_name="activity")
    op.drop_index(op.f("activity_created_at_idx"), table_name="activity")
    op.drop_index(op.f("activity_actor_id_idx"), table_name="activity")
    op.drop_table("activity")
