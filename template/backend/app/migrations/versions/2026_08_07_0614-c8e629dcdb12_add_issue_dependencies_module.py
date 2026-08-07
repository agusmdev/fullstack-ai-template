"""add issue dependencies module

Revision ID: c8e629dcdb12
Revises: 726abb558492
Create Date: 2026-08-07 06:14:26.033144

Creates the ``issue_dependency`` table — directional 'blocks' relationships
between two issues (``blocker_id`` → ``blocked_id``), with a compound unique
constraint on the pair (VAL-DEPS-001). Both FKs target ``issue`` with CASCADE
so deleting either endpoint removes the link.

Pre-existing user-table drift (email_verified_at TIMESTAMP vs DateTime,
user_email unique index) and missing project timestamp indexes are
intentionally NOT included — see AGENTS.md "Known Pre-Existing Issues".
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c8e629dcdb12"
down_revision: str | None = "726abb558492"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "issue_dependency",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("blocker_id", sa.Uuid(), nullable=False),
        sa.Column("blocked_id", sa.Uuid(), nullable=False),
        sa.Column(
            "relation",
            sa.String(length=32),
            server_default="blocks",
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["blocked_id"],
            ["issue.id"],
            name=op.f("issue_dependency_blocked_id_issue_fkey"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["blocker_id"],
            ["issue.id"],
            name=op.f("issue_dependency_blocker_id_issue_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("issue_dependency_pkey")),
        sa.UniqueConstraint(
            "blocker_id", "blocked_id", name="issue_dependency_pair_key"
        ),
    )
    op.create_index(
        op.f("issue_dependency_blocked_id_idx"),
        "issue_dependency",
        ["blocked_id"],
        unique=False,
    )
    op.create_index(
        op.f("issue_dependency_blocker_id_idx"),
        "issue_dependency",
        ["blocker_id"],
        unique=False,
    )
    op.create_index(
        op.f("issue_dependency_created_at_idx"),
        "issue_dependency",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("issue_dependency_updated_at_idx"),
        "issue_dependency",
        ["updated_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("issue_dependency_updated_at_idx"), table_name="issue_dependency"
    )
    op.drop_index(
        op.f("issue_dependency_created_at_idx"), table_name="issue_dependency"
    )
    op.drop_index(
        op.f("issue_dependency_blocker_id_idx"), table_name="issue_dependency"
    )
    op.drop_index(
        op.f("issue_dependency_blocked_id_idx"), table_name="issue_dependency"
    )
    op.drop_table("issue_dependency")
