"""Lowercase user emails

The API now stores and compares email addresses in lowercase (see
app.user.schemas.normalize_email). Rows written before that keep their case,
and their owners could no longer log in, so they are lowercased here.

If two accounts differ only in the case of their email, the unique
constraint stops this migration: merge or rename one of them first.

Revision ID: 16e70763045b
Revises: ad52dea13124
Create Date: 2026-10-12 12:01:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "16e70763045b"
down_revision = "ad52dea13124"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('UPDATE "user" SET email = lower(email) WHERE email <> lower(email)')


def downgrade() -> None:
    # The original case is gone; lowercase addresses are valid either way.
    pass
