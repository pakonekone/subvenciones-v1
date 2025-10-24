"""add google sheets fields

Revision ID: 002_google_sheets
Revises:
Create Date: 2025-10-24 23:45:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_google_sheets'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add Google Sheets tracking fields only if they don't exist
    from alembic import op
    import sqlalchemy as sa
    from sqlalchemy import inspect

    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('grants')]

    if 'google_sheets_exported' not in columns:
        op.add_column('grants', sa.Column('google_sheets_exported', sa.Boolean(), nullable=False, server_default='false'))

    if 'google_sheets_exported_at' not in columns:
        op.add_column('grants', sa.Column('google_sheets_exported_at', sa.DateTime(), nullable=True))

    if 'google_sheets_row_id' not in columns:
        op.add_column('grants', sa.Column('google_sheets_row_id', sa.String(), nullable=True))

    if 'google_sheets_url' not in columns:
        op.add_column('grants', sa.Column('google_sheets_url', sa.Text(), nullable=True))

    # Create index on google_sheets_exported for faster queries (only if not exists)
    indexes = [idx['name'] for idx in inspector.get_indexes('grants')]
    if 'ix_grants_google_sheets_exported' not in indexes:
        op.create_index(op.f('ix_grants_google_sheets_exported'), 'grants', ['google_sheets_exported'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_grants_google_sheets_exported'), table_name='grants')
    op.drop_column('grants', 'google_sheets_url')
    op.drop_column('grants', 'google_sheets_row_id')
    op.drop_column('grants', 'google_sheets_exported_at')
    op.drop_column('grants', 'google_sheets_exported')
