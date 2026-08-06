"""add issues module

Revision ID: 13f3d28051fb
Revises: c52a323e7c26
Create Date: 2026-08-06 16:52:08.942273

Creates the ``issue`` table (the core entity hub) and wires the deferred
``issue_label.issue_id → issue.id`` foreign-key constraint that was left
unconstrained by the labels module (m1-workflow-labels-backend).

Pre-existing user-table drift (email_verified_at TIMESTAMP vs DateTime,
user_email unique index) is intentionally NOT included — see AGENTS.md
"Known Pre-Existing Issues".
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "13f3d28051fb"
down_revision: str | None = "c52a323e7c26"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "issue",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("identifier", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status_id", sa.Uuid(), nullable=False),
        sa.Column("priority", sa.Integer(), server_default="4", nullable=False),
        sa.Column("assignee_id", sa.Uuid(), nullable=True),
        sa.Column("creator_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("cycle_id", sa.Uuid(), nullable=True),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("sort_order", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("estimate", sa.Float(), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["assignee_id"],
            ["user.id"],
            name=op.f("issue_assignee_id_user_fkey"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["creator_id"],
            ["user.id"],
            name=op.f("issue_creator_id_user_fkey"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["issue.id"],
            name=op.f("issue_parent_id_issue_fkey"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["status_id"],
            ["workflow_state.id"],
            name=op.f("issue_status_id_workflow_state_fkey"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["team_id"],
            ["team.id"],
            name=op.f("issue_team_id_team_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("issue_pkey")),
        sa.UniqueConstraint("team_id", "identifier", name="issue_team_identifier_key"),
    )
    op.create_index(
        op.f("issue_assignee_id_idx"), "issue", ["assignee_id"], unique=False
    )
    op.create_index(op.f("issue_created_at_idx"), "issue", ["created_at"], unique=False)
    op.create_index(op.f("issue_creator_id_idx"), "issue", ["creator_id"], unique=False)
    op.create_index(op.f("issue_cycle_id_idx"), "issue", ["cycle_id"], unique=False)
    op.create_index(op.f("issue_parent_id_idx"), "issue", ["parent_id"], unique=False)
    op.create_index(op.f("issue_project_id_idx"), "issue", ["project_id"], unique=False)
    op.create_index(op.f("issue_status_id_idx"), "issue", ["status_id"], unique=False)
    op.create_index(op.f("issue_team_id_idx"), "issue", ["team_id"], unique=False)
    op.create_index(op.f("issue_updated_at_idx"), "issue", ["updated_at"], unique=False)

    # Wire the deferred issue_label.issue_id → issue.id FK.
    op.create_foreign_key(
        op.f("issue_label_issue_id_issue_fkey"),
        "issue_label",
        "issue",
        ["issue_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("issue_label_issue_id_issue_fkey"),
        "issue_label",
        type_="foreignkey",
    )
    op.drop_index(op.f("issue_updated_at_idx"), table_name="issue")
    op.drop_index(op.f("issue_team_id_idx"), table_name="issue")
    op.drop_index(op.f("issue_status_id_idx"), table_name="issue")
    op.drop_index(op.f("issue_project_id_idx"), table_name="issue")
    op.drop_index(op.f("issue_parent_id_idx"), table_name="issue")
    op.drop_index(op.f("issue_cycle_id_idx"), table_name="issue")
    op.drop_index(op.f("issue_creator_id_idx"), table_name="issue")
    op.drop_index(op.f("issue_created_at_idx"), table_name="issue")
    op.drop_index(op.f("issue_assignee_id_idx"), table_name="issue")
    op.drop_table("issue")
