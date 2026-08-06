"""add workflow states, labels, and issue_label association

Revision ID: c52a323e7c26
Revises: e0224f807aee
Create Date: 2026-08-06 16:35:42.250324

Adds the WorkflowState and Label tables plus the issue_label association table.

NOTE (coordination with m1-issue-backend): ``issue_label.issue_id`` is a plain
UUID column here with NO foreign-key constraint, because the ``issue`` table does
not exist yet. m1-issue-backend must add the ``issue_label_issue_id_issue_fkey``
constraint (``op.create_foreign_key``) in its migration after creating the
``issue`` table, and add ``ForeignKey("issue.id", ondelete="CASCADE")`` to the
``issue_label.issue_id`` column in the model.

User-table drift detected by autogenerate (email_verified_at type, user_email
unique index) is pre-existing and intentionally NOT included here.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c52a323e7c26"
down_revision: str | None = "e0224f807aee"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create the workflow_state_type enum used by WorkflowState.type
    sa.Enum(
        "backlog",
        "unstarted",
        "started",
        "completed",
        "canceled",
        name="workflow_state_type",
    ).create(op.get_bind())

    op.create_table(
        "workflow_state",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "type",
            postgresql.ENUM(
                "backlog",
                "unstarted",
                "started",
                "completed",
                "canceled",
                name="workflow_state_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("position", sa.Float(), nullable=False),
        sa.Column("color", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["team_id"],
            ["team.id"],
            name=op.f("workflow_state_team_id_team_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("workflow_state_pkey")),
        sa.UniqueConstraint("team_id", "name", name="workflow_state_team_name_key"),
    )
    op.create_index(
        op.f("workflow_state_created_at_idx"),
        "workflow_state",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("workflow_state_team_id_idx"),
        "workflow_state",
        ["team_id"],
        unique=False,
    )
    op.create_index(
        op.f("workflow_state_updated_at_idx"),
        "workflow_state",
        ["updated_at"],
        unique=False,
    )

    op.create_table(
        "label",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("color", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["team_id"],
            ["team.id"],
            name=op.f("label_team_id_team_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("label_pkey")),
        sa.UniqueConstraint("team_id", "name", name="label_team_name_key"),
    )
    op.create_index(op.f("label_created_at_idx"), "label", ["created_at"], unique=False)
    op.create_index(op.f("label_team_id_idx"), "label", ["team_id"], unique=False)
    op.create_index(op.f("label_updated_at_idx"), "label", ["updated_at"], unique=False)

    # issue_label association (issue_id FK added later by m1-issue-backend).
    op.create_table(
        "issue_label",
        sa.Column("issue_id", sa.Uuid(), nullable=False),
        sa.Column("label_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["label_id"],
            ["label.id"],
            name=op.f("issue_label_label_id_label_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("issue_id", "label_id", name=op.f("issue_label_pkey")),
    )


def downgrade() -> None:
    op.drop_table("issue_label")

    op.drop_index(op.f("label_updated_at_idx"), table_name="label")
    op.drop_index(op.f("label_team_id_idx"), table_name="label")
    op.drop_index(op.f("label_created_at_idx"), table_name="label")
    op.drop_table("label")

    op.drop_index(op.f("workflow_state_updated_at_idx"), table_name="workflow_state")
    op.drop_index(op.f("workflow_state_team_id_idx"), table_name="workflow_state")
    op.drop_index(op.f("workflow_state_created_at_idx"), table_name="workflow_state")
    op.drop_table("workflow_state")

    sa.Enum(
        "backlog",
        "unstarted",
        "started",
        "completed",
        "canceled",
        name="workflow_state_type",
    ).drop(op.get_bind())
