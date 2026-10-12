"""Timezone-aware token timestamps

The expiry and use times of sessions, password reset tokens and email
verification tokens were naive TIMESTAMP columns written with the server's
local clock. They are now TIMESTAMP WITH TIME ZONE, like every other
timestamp. Existing values were written by servers that run in UTC (the
Docker images), so they are read as UTC.

Revision ID: ad52dea13124
Revises: a1b2c3d4e5f6
Create Date: 2026-10-12 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ad52dea13124"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None

# (table, column, nullable)
COLUMNS = [
    ("session", "expires_at", False),
    ("password_reset_token", "expires_at", False),
    ("password_reset_token", "used_at", True),
    ("email_verification_token", "expires_at", False),
    ("email_verification_token", "used_at", True),
]


def upgrade() -> None:
    for table, column, nullable in COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.TIMESTAMP(timezone=True),
            existing_type=sa.TIMESTAMP(),
            existing_nullable=nullable,
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )


def downgrade() -> None:
    for table, column, nullable in COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.TIMESTAMP(),
            existing_type=sa.TIMESTAMP(timezone=True),
            existing_nullable=nullable,
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )
