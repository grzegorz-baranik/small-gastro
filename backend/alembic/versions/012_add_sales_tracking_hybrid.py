"""Add sales tracking hybrid feature

Revision ID: 012
Revises: 011
Create Date: 2026-01-06

This migration adds support for the hybrid sales tracking feature:
- Product categories for organizing menu items
- Recorded sales table for real-time sales tracking
- Revenue discrepancy tracking in daily_records
- Category assignment for products
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '012'
down_revision: Union[str, None] = '011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # STEP 1: Create product_categories table
    # =========================================================================
    op.create_table(
        'product_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_product_categories_name'),
    )
    op.create_index(op.f('ix_product_categories_id'), 'product_categories', ['id'], unique=False)

    # =========================================================================
    # STEP 2: Create recorded_sales table
    # =========================================================================
    op.create_table(
        'recorded_sales',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('daily_record_id', sa.Integer(), nullable=False),
        sa.Column('product_variant_id', sa.Integer(), nullable=False),
        sa.Column('shift_assignment_id', sa.Integer(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('unit_price_pln', sa.Numeric(10, 2), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('voided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('void_reason', sa.String(50), nullable=True),
        sa.Column('void_notes', sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(
            ['daily_record_id'], ['daily_records.id'],
            name='fk_recorded_sales_daily_record_id',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['product_variant_id'], ['product_variants.id'],
            name='fk_recorded_sales_product_variant_id',
            ondelete='RESTRICT'
        ),
        sa.ForeignKeyConstraint(
            ['shift_assignment_id'], ['shift_assignments.id'],
            name='fk_recorded_sales_shift_assignment_id',
            ondelete='SET NULL'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('quantity > 0', name='check_recorded_sales_quantity_positive'),
        sa.CheckConstraint('unit_price_pln > 0', name='check_recorded_sales_price_positive'),
        sa.CheckConstraint(
            "void_reason IN ('mistake', 'customer_refund', 'duplicate', 'other') OR void_reason IS NULL",
            name='check_recorded_sales_void_reason_valid'
        ),
    )
    op.create_index(op.f('ix_recorded_sales_id'), 'recorded_sales', ['id'], unique=False)
    op.create_index('idx_recorded_sales_daily_record', 'recorded_sales', ['daily_record_id'], unique=False)
    op.create_index('idx_recorded_sales_variant', 'recorded_sales', ['product_variant_id'], unique=False)
    op.create_index('idx_recorded_sales_recorded_at', 'recorded_sales', ['recorded_at'], unique=False)

    # =========================================================================
    # STEP 3: Add category_id column to products table
    # =========================================================================
    op.add_column(
        'products',
        sa.Column('category_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_products_category_id',
        'products', 'product_categories',
        ['category_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('idx_products_category', 'products', ['category_id'], unique=False)

    # =========================================================================
    # STEP 4: Add revenue tracking columns to daily_records table
    # =========================================================================
    op.add_column(
        'daily_records',
        sa.Column('recorded_revenue_pln', sa.Numeric(10, 2), nullable=True)
    )
    op.add_column(
        'daily_records',
        sa.Column('calculated_revenue_pln', sa.Numeric(10, 2), nullable=True)
    )
    op.add_column(
        'daily_records',
        sa.Column('revenue_discrepancy_pln', sa.Numeric(10, 2), nullable=True)
    )
    op.add_column(
        'daily_records',
        sa.Column('revenue_source', sa.String(20), nullable=True, server_default='calculated')
    )
    op.create_check_constraint(
        'check_daily_records_revenue_source_valid',
        'daily_records',
        "revenue_source IN ('recorded', 'calculated', 'hybrid')"
    )

    # =========================================================================
    # STEP 5: Seed product_categories with default values
    # =========================================================================
    op.execute("""
        INSERT INTO product_categories (name, sort_order) VALUES
        ('Kebaby', 1),
        ('Zapiekanki', 2),
        ('Hot-Dogi', 3),
        ('Frytki', 4),
        ('Napoje', 5)
    """)


def downgrade() -> None:
    # =========================================================================
    # STEP 1: Remove check constraint from daily_records
    # =========================================================================
    op.drop_constraint('check_daily_records_revenue_source_valid', 'daily_records', type_='check')

    # =========================================================================
    # STEP 2: Remove revenue tracking columns from daily_records
    # =========================================================================
    op.drop_column('daily_records', 'revenue_source')
    op.drop_column('daily_records', 'revenue_discrepancy_pln')
    op.drop_column('daily_records', 'calculated_revenue_pln')
    op.drop_column('daily_records', 'recorded_revenue_pln')

    # =========================================================================
    # STEP 3: Remove category_id from products table
    # =========================================================================
    op.drop_index('idx_products_category', table_name='products')
    op.drop_constraint('fk_products_category_id', 'products', type_='foreignkey')
    op.drop_column('products', 'category_id')

    # =========================================================================
    # STEP 4: Drop recorded_sales table
    # =========================================================================
    op.drop_index('idx_recorded_sales_recorded_at', table_name='recorded_sales')
    op.drop_index('idx_recorded_sales_variant', table_name='recorded_sales')
    op.drop_index('idx_recorded_sales_daily_record', table_name='recorded_sales')
    op.drop_index(op.f('ix_recorded_sales_id'), table_name='recorded_sales')
    op.drop_table('recorded_sales')

    # =========================================================================
    # STEP 5: Drop product_categories table
    # =========================================================================
    op.drop_index(op.f('ix_product_categories_id'), table_name='product_categories')
    op.drop_table('product_categories')
