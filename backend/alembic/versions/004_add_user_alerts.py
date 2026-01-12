"""Add user_alerts table

Revision ID: 004_user_alerts
Revises: 003_user_favorites
Create Date: 2026-01-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_user_alerts'
down_revision: Union[str, Sequence[str], None] = '003_user_favorites'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create user_alerts table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'user_alerts' not in tables:
        op.create_table('user_alerts',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('email', sa.String(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
            sa.Column('keywords', sa.Text(), nullable=True),
            sa.Column('source', sa.String(), nullable=True),
            sa.Column('min_budget', sa.Float(), nullable=True),
            sa.Column('max_budget', sa.Float(), nullable=True),
            sa.Column('is_nonprofit', sa.Boolean(), nullable=True),
            sa.Column('regions', sa.JSON(), nullable=True),
            sa.Column('sectors', sa.JSON(), nullable=True),
            sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
            sa.Column('matches_count', sa.Integer(), nullable=True, default=0),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_user_alerts_id'), 'user_alerts', ['id'], unique=False)
        op.create_index(op.f('ix_user_alerts_user_id'), 'user_alerts', ['user_id'], unique=False)
        op.create_index(op.f('ix_user_alerts_is_active'), 'user_alerts', ['is_active'], unique=False)
        op.create_index(op.f('ix_user_alerts_created_at'), 'user_alerts', ['created_at'], unique=False)


def downgrade() -> None:
    """Drop user_alerts table."""
    op.drop_index(op.f('ix_user_alerts_created_at'), table_name='user_alerts')
    op.drop_index(op.f('ix_user_alerts_is_active'), table_name='user_alerts')
    op.drop_index(op.f('ix_user_alerts_user_id'), table_name='user_alerts')
    op.drop_index(op.f('ix_user_alerts_id'), table_name='user_alerts')
    op.drop_table('user_alerts')
