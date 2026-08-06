"""remove items, add teams and team_memberships

Revision ID: e0224f807aee
Revises: a1b2c3d4e5f6
Create Date: 2026-08-06 14:12:50.225298

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e0224f807aee"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create the team_role enum used by TeamMembership.role
    sa.Enum("admin", "member", "guest", name="team_role").create(op.get_bind())

    op.create_table(
        "team",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("key", sa.String(length=10), nullable=False),
        sa.Column("issue_sequence", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("team_pkey")),
    )
    op.create_index(op.f("team_created_at_idx"), "team", ["created_at"], unique=False)
    op.create_index(op.f("team_key_idx"), "team", ["key"], unique=True)
    op.create_index(op.f("team_updated_at_idx"), "team", ["updated_at"], unique=False)

    op.create_table(
        "team_membership",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM(
                "admin", "member", "guest", name="team_role", create_type=False
            ),
            server_default="member",
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["team_id"],
            ["team.id"],
            name=op.f("team_membership_team_id_team_fkey"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name=op.f("team_membership_user_id_user_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("team_membership_pkey")),
        sa.UniqueConstraint("user_id", "team_id", name="team_membership_user_team_key"),
    )
    op.create_index(
        op.f("team_membership_created_at_idx"),
        "team_membership",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("team_membership_team_id_idx"),
        "team_membership",
        ["team_id"],
        unique=False,
    )
    op.create_index(
        op.f("team_membership_updated_at_idx"),
        "team_membership",
        ["updated_at"],
        unique=False,
    )
    op.create_index(
        op.f("team_membership_user_id_idx"),
        "team_membership",
        ["user_id"],
        unique=False,
    )

    # Drop the legacy items table
    op.drop_index(op.f("item_created_at_idx"), table_name="item")
    op.drop_index(op.f("item_sku_idx"), table_name="item")
    op.drop_index(op.f("item_updated_at_idx"), table_name="item")
    op.drop_index(op.f("item_user_id_idx"), table_name="item")
    op.drop_table("item")


def downgrade() -> None:
    # Recreate the legacy items table
    op.create_table(
        "item",
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("sku", sa.VARCHAR(length=100), autoincrement=False, nullable=True),
        sa.Column("name", sa.VARCHAR(length=255), autoincrement=False, nullable=False),
        sa.Column("description", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column("quantity", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("user_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("item_user_id_fkey"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("item_pkey")),
        sa.UniqueConstraint(
            "sku",
            name=op.f("item_sku_key"),
            postgresql_include=[],
            postgresql_nulls_not_distinct=False,
        ),
    )
    op.create_index(op.f("item_user_id_idx"), "item", ["user_id"], unique=False)
    op.create_index(op.f("item_updated_at_idx"), "item", ["updated_at"], unique=False)
    op.create_index(op.f("item_sku_idx"), "item", ["sku"], unique=False)
    op.create_index(op.f("item_created_at_idx"), "item", ["created_at"], unique=False)

    # Drop team tables
    op.drop_index(op.f("team_membership_user_id_idx"), table_name="team_membership")
    op.drop_index(op.f("team_membership_updated_at_idx"), table_name="team_membership")
    op.drop_index(op.f("team_membership_team_id_idx"), table_name="team_membership")
    op.drop_index(op.f("team_membership_created_at_idx"), table_name="team_membership")
    op.drop_table("team_membership")
    op.drop_index(op.f("team_updated_at_idx"), table_name="team")
    op.drop_index(op.f("team_key_idx"), table_name="team")
    op.drop_index(op.f("team_created_at_idx"), table_name="team")
    op.drop_table("team")
    sa.Enum("admin", "member", "guest", name="team_role").drop(op.get_bind())
