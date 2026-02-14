"""Add is_default and updated_at columns to product_variants table

Revision ID: 008
Revises: 006
Create Date: 2026-01-04

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '008'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_default column with default false
    op.add_column('product_variants', sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'))

    # Add updated_at column with current timestamp
    op.add_column('product_variants', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()))

    # Set first variant of each product as default
    op.execute("""
        UPDATE product_variants pv
        SET is_default = true
        WHERE id = (
            SELECT MIN(id) FROM product_variants pv2
            WHERE pv2.product_id = pv.product_id
        )
    """)


def downgrade() -> None:
    op.drop_column('product_variants', 'updated_at')
    op.drop_column('product_variants', 'is_default')
