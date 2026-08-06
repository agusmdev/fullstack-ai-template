"""add cycles module

Revision ID: 8d11d0d28d6f
Revises: a4b5c6d7e8f9
Create Date: 2026-08-06 20:15:47.644413

Creates the ``cycle`` table (team-scoped time-boxed sprints) and wires the
deferred ``issue.cycle_id → cycle.id`` foreign-key constraint (left
unconstrained by m1-issue-backend because the ``cycle`` table did not exist
yet). The FK uses ``ondelete=SET NULL`` so deleting a cycle detaches its
issues rather than cascading (VAL-CYCLES-005).

Pre-existing user-table drift (email_verified_at TIMESTAMP vs DateTime,
user_email unique index) and missing project timestamp indexes are
intentionally NOT included — see AGENTS.md "Known Pre-Existing Issues".
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8d11d0d28d6f"
down_revision: str | None = "a4b5c6d7e8f9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cycle",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("starts_at", sa.Date(), nullable=False),
        sa.Column("ends_at", sa.Date(), nullable=False),
        sa.Column("completed_at", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["team_id"],
            ["team.id"],
            name=op.f("cycle_team_id_team_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("cycle_pkey")),
        sa.UniqueConstraint("team_id", "name", name="cycle_team_name_key"),
    )
    op.create_index(op.f("cycle_created_at_idx"), "cycle", ["created_at"], unique=False)
    op.create_index(op.f("cycle_team_id_idx"), "cycle", ["team_id"], unique=False)
    op.create_index(op.f("cycle_updated_at_idx"), "cycle", ["updated_at"], unique=False)

    # Wire the deferred issue.cycle_id → cycle.id FK.
    op.create_foreign_key(
        op.f("issue_cycle_id_cycle_fkey"),
        "issue",
        "cycle",
        ["cycle_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("issue_cycle_id_cycle_fkey"),
        "issue",
        type_="foreignkey",
    )
    op.drop_index(op.f("cycle_updated_at_idx"), table_name="cycle")
    op.drop_index(op.f("cycle_team_id_idx"), table_name="cycle")
    op.drop_index(op.f("cycle_created_at_idx"), table_name="cycle")
    op.drop_table("cycle")
