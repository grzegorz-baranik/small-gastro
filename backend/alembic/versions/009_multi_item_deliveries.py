"""Restructure deliveries to support multiple items per delivery

Revision ID: 009
Revises: 008
Create Date: 2026-01-04

This migration:
1. Restructures the deliveries table for invoice-level data
2. Creates delivery_items table for ingredient lines
3. Migrates existing deliveries (one delivery -> one delivery_item)
4. Adds invoice fields (supplier_name, invoice_number, total_cost_pln, notes)
5. Adds transaction_id FK for auto-expense linking
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '009'
down_revision: Union[str, None] = '008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # STEP 1: Add new columns to deliveries table (nullable for now)
    # =========================================================================
    op.add_column('deliveries', sa.Column('supplier_name', sa.String(255), nullable=True))
    op.add_column('deliveries', sa.Column('invoice_number', sa.String(100), nullable=True))
    op.add_column('deliveries', sa.Column('notes', sa.Text(), nullable=True))
    op.add_column('deliveries', sa.Column('total_cost_pln', sa.Numeric(10, 2), nullable=True))
    op.add_column('deliveries', sa.Column(
        'transaction_id',
        sa.Integer(),
        sa.ForeignKey('transactions.id', ondelete='SET NULL'),
        nullable=True
    ))

    # =========================================================================
    # STEP 2: Create delivery_items table
    # =========================================================================
    op.create_table(
        'delivery_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('delivery_id', sa.Integer(), nullable=False),
        sa.Column('ingredient_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('cost_pln', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['delivery_id'], ['deliveries.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('quantity > 0', name='check_delivery_item_quantity_positive'),
        sa.CheckConstraint('cost_pln IS NULL OR cost_pln >= 0', name='check_delivery_item_cost_non_negative')
    )
    op.create_index(op.f('ix_delivery_items_id'), 'delivery_items', ['id'], unique=False)
    op.create_index('ix_delivery_items_delivery_id', 'delivery_items', ['delivery_id'], unique=False)

    # =========================================================================
    # STEP 3: Migrate existing data
    # For each old delivery, create a delivery_item and copy price_pln to total_cost_pln
    # =========================================================================
    op.execute("""
        INSERT INTO delivery_items (delivery_id, ingredient_id, quantity, cost_pln, created_at)
        SELECT id, ingredient_id, quantity, price_pln, created_at
        FROM deliveries
        WHERE ingredient_id IS NOT NULL
    """)

    op.execute("""
        UPDATE deliveries
        SET total_cost_pln = price_pln
        WHERE price_pln IS NOT NULL
    """)

    # =========================================================================
    # STEP 4: Drop old columns and constraints from deliveries
    # =========================================================================
    # Drop old check constraints first
    op.drop_constraint('check_delivery_quantity_positive', 'deliveries', type_='check')
    op.drop_constraint('check_delivery_price_non_negative', 'deliveries', type_='check')

    # Drop foreign key constraint for ingredient_id
    op.drop_constraint('deliveries_ingredient_id_fkey', 'deliveries', type_='foreignkey')

    # Drop old columns
    op.drop_column('deliveries', 'ingredient_id')
    op.drop_column('deliveries', 'quantity')
    op.drop_column('deliveries', 'price_pln')

    # =========================================================================
    # STEP 5: Make total_cost_pln NOT NULL and add check constraint
    # =========================================================================
    op.alter_column('deliveries', 'total_cost_pln', nullable=False)
    op.create_check_constraint(
        'check_delivery_total_cost_non_negative',
        'deliveries',
        'total_cost_pln >= 0'
    )

    # Create index for transaction_id
    op.create_index('ix_deliveries_transaction_id', 'deliveries', ['transaction_id'], unique=False)


def downgrade() -> None:
    # =========================================================================
    # STEP 1: Add back old columns to deliveries (nullable for now)
    # =========================================================================
    op.add_column('deliveries', sa.Column('ingredient_id', sa.Integer(), nullable=True))
    op.add_column('deliveries', sa.Column('quantity', sa.Numeric(10, 3), nullable=True))
    op.add_column('deliveries', sa.Column('price_pln', sa.Numeric(10, 2), nullable=True))

    # Add back foreign key for ingredient_id
    op.create_foreign_key(
        'deliveries_ingredient_id_fkey',
        'deliveries', 'ingredients',
        ['ingredient_id'], ['id'],
        ondelete='RESTRICT'
    )

    # =========================================================================
    # STEP 2: Migrate data back from delivery_items
    # Take the first item from each delivery
    # =========================================================================
    op.execute("""
        UPDATE deliveries d
        SET
            ingredient_id = di.ingredient_id,
            quantity = di.quantity,
            price_pln = COALESCE(di.cost_pln, d.total_cost_pln)
        FROM (
            SELECT DISTINCT ON (delivery_id) delivery_id, ingredient_id, quantity, cost_pln
            FROM delivery_items
            ORDER BY delivery_id, id
        ) di
        WHERE d.id = di.delivery_id
    """)

    # =========================================================================
    # STEP 3: Drop new columns and table
    # =========================================================================
    op.drop_index('ix_deliveries_transaction_id', 'deliveries')
    op.drop_constraint('check_delivery_total_cost_non_negative', 'deliveries', type_='check')

    op.drop_column('deliveries', 'transaction_id')
    op.drop_column('deliveries', 'notes')
    op.drop_column('deliveries', 'invoice_number')
    op.drop_column('deliveries', 'supplier_name')
    op.drop_column('deliveries', 'total_cost_pln')

    # Drop delivery_items table
    op.drop_index('ix_delivery_items_delivery_id', 'delivery_items')
    op.drop_index(op.f('ix_delivery_items_id'), 'delivery_items')
    op.drop_table('delivery_items')

    # =========================================================================
    # STEP 4: Make old columns NOT NULL and add constraints
    # =========================================================================
    op.alter_column('deliveries', 'ingredient_id', nullable=False)
    op.alter_column('deliveries', 'quantity', nullable=False)
    op.alter_column('deliveries', 'price_pln', nullable=False)

    op.create_check_constraint(
        'check_delivery_quantity_positive',
        'deliveries',
        'quantity > 0'
    )
    op.create_check_constraint(
        'check_delivery_price_non_negative',
        'deliveries',
        'price_pln >= 0'
    )
