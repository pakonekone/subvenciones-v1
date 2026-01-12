"""Add user_favorites table

Revision ID: 003_user_favorites
Revises: ac1ba32b6d3b
Create Date: 2026-01-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_user_favorites'
down_revision: Union[str, Sequence[str], None] = 'ac1ba32b6d3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create user_favorites table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'user_favorites' not in tables:
        op.create_table('user_favorites',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('grant_id', sa.String(), nullable=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['grant_id'], ['grants.id'], ondelete='CASCADE')
        )
        op.create_index(op.f('ix_user_favorites_id'), 'user_favorites', ['id'], unique=False)
        op.create_index(op.f('ix_user_favorites_user_id'), 'user_favorites', ['user_id'], unique=False)
        op.create_index(op.f('ix_user_favorites_grant_id'), 'user_favorites', ['grant_id'], unique=False)
        op.create_index(op.f('ix_user_favorites_created_at'), 'user_favorites', ['created_at'], unique=False)


def downgrade() -> None:
    """Drop user_favorites table."""
    op.drop_index(op.f('ix_user_favorites_created_at'), table_name='user_favorites')
    op.drop_index(op.f('ix_user_favorites_grant_id'), table_name='user_favorites')
    op.drop_index(op.f('ix_user_favorites_user_id'), table_name='user_favorites')
    op.drop_index(op.f('ix_user_favorites_id'), table_name='user_favorites')
    op.drop_table('user_favorites')
