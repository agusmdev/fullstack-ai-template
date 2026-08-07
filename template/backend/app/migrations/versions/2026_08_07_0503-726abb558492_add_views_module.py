"""add views module

Revision ID: 726abb558492
Revises: 8d11d0d28d6f
Create Date: 2026-08-07 05:03:38.964867

Creates the ``view`` table — saved issue views (filters JSONB + group_by +
order_by), team-scoped (CASCADE) with an owner (SET NULL) for attribution.

Pre-existing user-table drift (email_verified_at TIMESTAMP vs DateTime,
user_email unique index) and missing project timestamp indexes are
intentionally NOT included — see AGENTS.md "Known Pre-Existing Issues".
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "726abb558492"
down_revision: str | None = "8d11d0d28d6f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "view",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=True),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "filters",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("group_by", sa.String(length=64), nullable=True),
        sa.Column("order_by", sa.String(length=64), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["user.id"],
            name=op.f("view_owner_id_user_fkey"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["team_id"],
            ["team.id"],
            name=op.f("view_team_id_team_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("view_pkey")),
    )
    op.create_index(op.f("view_created_at_idx"), "view", ["created_at"], unique=False)
    op.create_index(op.f("view_owner_id_idx"), "view", ["owner_id"], unique=False)
    op.create_index(op.f("view_team_id_idx"), "view", ["team_id"], unique=False)
    op.create_index(op.f("view_updated_at_idx"), "view", ["updated_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("view_updated_at_idx"), table_name="view")
    op.drop_index(op.f("view_team_id_idx"), table_name="view")
    op.drop_index(op.f("view_owner_id_idx"), table_name="view")
    op.drop_index(op.f("view_created_at_idx"), table_name="view")
    op.drop_table("view")
