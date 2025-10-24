"""add bdns_documents column

Revision ID: 001
Revises:
Create Date: 2025-10-20 08:15:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add bdns_documents JSON column to grants table."""
    op.add_column('grants', sa.Column('bdns_documents', postgresql.JSON(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    """Remove bdns_documents column from grants table."""
    op.drop_column('grants', 'bdns_documents')
