"""Add organization_profiles table

Revision ID: 005_organization_profiles
Revises: 004_user_alerts
Create Date: 2026-01-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '005_organization_profiles'
down_revision: Union[str, Sequence[str], None] = '004_user_alerts'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create organization_profiles table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'organization_profiles' not in tables:
        op.create_table('organization_profiles',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('cif', sa.String(), nullable=True),
            sa.Column('organization_type', sa.String(), nullable=True),
            sa.Column('sectors', sa.JSON(), nullable=True),
            sa.Column('regions', sa.JSON(), nullable=True),
            sa.Column('annual_budget', sa.Float(), nullable=True),
            sa.Column('employee_count', sa.Integer(), nullable=True),
            sa.Column('founding_year', sa.Integer(), nullable=True),
            sa.Column('capabilities', sa.JSON(), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_organization_profiles_user_id'), 'organization_profiles', ['user_id'], unique=True)


def downgrade() -> None:
    """Drop organization_profiles table."""
    op.drop_index(op.f('ix_organization_profiles_user_id'), table_name='organization_profiles')
    op.drop_table('organization_profiles')
