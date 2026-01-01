"""Add index on expense_categories.parent_id

Revision ID: 002
Revises: 001
Create Date: 2024-01-02

"""
from typing import Sequence, Union
from alembic import op

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('idx_expense_categories_parent', 'expense_categories', ['parent_id'])


def downgrade() -> None:
    op.drop_index('idx_expense_categories_parent', table_name='expense_categories')
