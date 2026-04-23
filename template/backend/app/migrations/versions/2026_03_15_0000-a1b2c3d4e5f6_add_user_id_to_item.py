"""Add user_id to item

Revision ID: a1b2c3d4e5f6
Revises: 6f253e9043e9
Create Date: 2026-03-15 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '6f253e9043e9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'item',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    )
    op.create_foreign_key(
        'item_user_id_fkey',
        'item', 'user',
        ['user_id'], ['id'],
        ondelete='CASCADE',
    )
    op.create_index('item_user_id_idx', 'item', ['user_id'])


def downgrade() -> None:
    op.drop_index('item_user_id_idx', table_name='item')
    op.drop_constraint('item_user_id_fkey', 'item', type_='foreignkey')
    op.drop_column('item', 'user_id')
