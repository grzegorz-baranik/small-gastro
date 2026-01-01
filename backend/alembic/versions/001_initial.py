"""Initial migration

Revision ID: 001
Revises:
Create Date: 2024-01-01

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ingredients table
    op.create_table(
        'ingredients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('unit_type', sa.Enum('weight', 'count', name='unittype'), nullable=False),
        sa.Column('current_stock_grams', sa.Numeric(precision=10, scale=2), server_default='0'),
        sa.Column('current_stock_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_ingredients_id'), 'ingredients', ['id'], unique=False)

    # Products table
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_products_id'), 'products', ['id'], unique=False)

    # Product ingredients junction table
    op.create_table(
        'product_ingredients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('ingredient_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id', 'ingredient_id')
    )
    op.create_index(op.f('ix_product_ingredients_id'), 'product_ingredients', ['id'], unique=False)

    # Expense categories table
    op.create_table(
        'expense_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.CheckConstraint('level >= 1 AND level <= 3', name='check_level_range'),
        sa.ForeignKeyConstraint(['parent_id'], ['expense_categories.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_expense_categories_id'), 'expense_categories', ['id'], unique=False)

    # Daily records table
    op.create_table(
        'daily_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('status', sa.Enum('open', 'closed', name='daystatus'), nullable=False, server_default='open'),
        sa.Column('opened_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date')
    )
    op.create_index(op.f('ix_daily_records_id'), 'daily_records', ['id'], unique=False)

    # Inventory snapshots table
    op.create_table(
        'inventory_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('daily_record_id', sa.Integer(), nullable=False),
        sa.Column('ingredient_id', sa.Integer(), nullable=False),
        sa.Column('snapshot_type', sa.Enum('open', 'close', name='snapshottype'), nullable=False),
        sa.Column('quantity_grams', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('quantity_count', sa.Integer(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['daily_record_id'], ['daily_records.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('daily_record_id', 'ingredient_id', 'snapshot_type', name='uq_snapshot_per_day_ingredient_type')
    )
    op.create_index(op.f('ix_inventory_snapshots_id'), 'inventory_snapshots', ['id'], unique=False)

    # Sales items table
    op.create_table(
        'sales_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('daily_record_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantity_sold', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('total_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['daily_record_id'], ['daily_records.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sales_items_id'), 'sales_items', ['id'], unique=False)

    # Transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type', sa.Enum('expense', 'revenue', name='transactiontype'), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('payment_method', sa.Enum('cash', 'card', 'bank_transfer', name='paymentmethod'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('transaction_date', sa.Date(), nullable=False),
        sa.Column('daily_record_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['category_id'], ['expense_categories.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['daily_record_id'], ['daily_records.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transactions_id'), 'transactions', ['id'], unique=False)
    op.create_index('idx_transactions_date', 'transactions', ['transaction_date'], unique=False)
    op.create_index('idx_transactions_type', 'transactions', ['type'], unique=False)


def downgrade() -> None:
    op.drop_table('transactions')
    op.drop_table('sales_items')
    op.drop_table('inventory_snapshots')
    op.drop_table('daily_records')
    op.drop_table('expense_categories')
    op.drop_table('product_ingredients')
    op.drop_table('products')
    op.drop_table('ingredients')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS transactiontype')
    op.execute('DROP TYPE IF EXISTS paymentmethod')
    op.execute('DROP TYPE IF EXISTS snapshottype')
    op.execute('DROP TYPE IF EXISTS daystatus')
    op.execute('DROP TYPE IF EXISTS unittype')
