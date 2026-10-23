"""add_chunk_embedding

Revision ID: 0002_add_chunk_embedding
Revises: 0001_initial_schema
Create Date: 2026-10-23 01:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0002_add_chunk_embedding'
down_revision: Union[str, None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('chunks') as batch_op:
        batch_op.add_column(sa.Column('embedding', sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('chunks') as batch_op:
        batch_op.drop_column('embedding')
