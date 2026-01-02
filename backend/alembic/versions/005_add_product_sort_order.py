"""Add sort_order column to products table

Revision ID: 005
Revises: 004
Create Date: 2026-01-02

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add sort_order column with default 0
    op.add_column('products', sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'))

    # Set initial sort_order based on id to preserve current order
    op.execute("UPDATE products SET sort_order = id")

    # Create index for efficient sorting
    op.create_index('idx_products_sort_order', 'products', ['sort_order'])


def downgrade() -> None:
    op.drop_index('idx_products_sort_order', table_name='products')
    op.drop_column('products', 'sort_order')
