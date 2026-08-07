"""add projects module

Revision ID: a4b5c6d7e8f9
Revises: 13f3d28051fb
Create Date: 2026-08-06 19:50:00.000000

Creates the ``project`` table (team-scoped collections of related issues) and
wires the deferred ``issue.project_id → project.id`` foreign-key constraint
(left unconstrained by m1-issue-backend because the ``project`` table did not
exist yet). The FK uses ``ondelete=SET NULL`` so deleting a project detaches its
issues rather than cascading (VAL-PROJECTS-008).

Pre-existing user-table drift (email_verified_at TIMESTAMP vs DateTime,
user_email unique index) is intentionally NOT included — see AGENTS.md
"Known Pre-Existing Issues".
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a4b5c6d7e8f9"
down_revision: str | None = "13f3d28051fb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "project",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "planned", "started", "completed", "canceled", name="project_status"
            ),
            server_default="planned",
            nullable=False,
        ),
        sa.Column("lead_id", sa.Uuid(), nullable=True),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["lead_id"],
            ["user.id"],
            name=op.f("project_lead_id_user_fkey"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["team_id"],
            ["team.id"],
            name=op.f("project_team_id_team_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("project_pkey")),
        sa.UniqueConstraint("team_id", "name", name="project_team_name_key"),
    )
    op.create_index(op.f("project_lead_id_idx"), "project", ["lead_id"], unique=False)
    op.create_index(op.f("project_team_id_idx"), "project", ["team_id"], unique=False)

    # Wire the deferred issue.project_id → project.id FK.
    op.create_foreign_key(
        op.f("issue_project_id_project_fkey"),
        "issue",
        "project",
        ["project_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("issue_project_id_project_fkey"),
        "issue",
        type_="foreignkey",
    )
    op.drop_index(op.f("project_team_id_idx"), table_name="project")
    op.drop_index(op.f("project_lead_id_idx"), table_name="project")
    op.drop_table("project")
    # Drop the enum type created with the table.
    sa.Enum(name="project_status").drop(op.get_bind(), checkfirst=True)
