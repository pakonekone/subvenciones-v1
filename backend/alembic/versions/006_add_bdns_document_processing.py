"""Add BDNS document processing fields

Revision ID: 006_bdns_document_processing
Revises: 005_organization_profiles
Create Date: 2026-01-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '006_bdns_document_processing'
down_revision: Union[str, Sequence[str], None] = '005_organization_profiles'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add BDNS document processing fields to grants table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('grants')]

    if 'bdns_documents_processed' not in columns:
        op.add_column('grants', sa.Column('bdns_documents_processed', sa.Boolean(), default=False))

    if 'bdns_documents_processed_at' not in columns:
        op.add_column('grants', sa.Column('bdns_documents_processed_at', sa.DateTime(), nullable=True))

    if 'bdns_documents_content' not in columns:
        op.add_column('grants', sa.Column('bdns_documents_content', sa.JSON(), nullable=True))

    if 'bdns_documents_combined_text' not in columns:
        op.add_column('grants', sa.Column('bdns_documents_combined_text', sa.Text(), nullable=True))

    # Create index for efficient querying of unprocessed documents
    op.create_index(
        'ix_grants_bdns_documents_processed',
        'grants',
        ['bdns_documents_processed'],
        if_not_exists=True
    )


def downgrade() -> None:
    """Remove BDNS document processing fields."""
    op.drop_index('ix_grants_bdns_documents_processed', table_name='grants')
    op.drop_column('grants', 'bdns_documents_combined_text')
    op.drop_column('grants', 'bdns_documents_content')
    op.drop_column('grants', 'bdns_documents_processed_at')
    op.drop_column('grants', 'bdns_documents_processed')
