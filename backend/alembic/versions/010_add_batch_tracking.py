"""Add batch tracking for ingredients with expiry dates

Revision ID: 010
Revises: 009
Create Date: 2026-01-05

This migration:
1. Creates ingredient_batches table for tracking batches with expiry dates
2. Creates batch_deductions table for audit trail of batch usage
3. Adds expiry_date to delivery_items
4. Adds batch_id FK to spoilages for linking spoilage to specific batches
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '010'
down_revision: Union[str, None] = '009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # STEP 1: Add expiry_date to delivery_items
    # =========================================================================
    op.add_column('delivery_items', sa.Column('expiry_date', sa.Date(), nullable=True))

    # =========================================================================
    # STEP 2: Create ingredient_batches table
    # =========================================================================
    op.create_table(
        'ingredient_batches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('batch_number', sa.String(20), nullable=False),
        sa.Column('ingredient_id', sa.Integer(), nullable=False),
        sa.Column('delivery_item_id', sa.Integer(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('initial_quantity', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('remaining_quantity', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('location', sa.String(20), nullable=False, server_default='storage'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['delivery_item_id'], ['delivery_items.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('batch_number', name='uq_ingredient_batches_batch_number'),
        sa.CheckConstraint('initial_quantity > 0', name='check_batch_initial_quantity_positive'),
        sa.CheckConstraint('remaining_quantity >= 0', name='check_batch_remaining_quantity_non_negative'),
        sa.CheckConstraint("location IN ('storage', 'shop')", name='check_batch_location_valid')
    )
    op.create_index(op.f('ix_ingredient_batches_id'), 'ingredient_batches', ['id'], unique=False)
    op.create_index('ix_ingredient_batches_ingredient_id', 'ingredient_batches', ['ingredient_id'], unique=False)
    op.create_index('ix_ingredient_batches_expiry_date', 'ingredient_batches', ['expiry_date'], unique=False)
    op.create_index('ix_ingredient_batches_batch_number', 'ingredient_batches', ['batch_number'], unique=False)

    # =========================================================================
    # STEP 3: Create batch_deductions table (audit trail)
    # =========================================================================
    op.create_table(
        'batch_deductions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('batch_id', sa.Integer(), nullable=False),
        sa.Column('daily_record_id', sa.Integer(), nullable=True),
        sa.Column('quantity', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('reason', sa.String(50), nullable=False),
        sa.Column('reference_type', sa.String(50), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['batch_id'], ['ingredient_batches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['daily_record_id'], ['daily_records.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('quantity > 0', name='check_batch_deduction_quantity_positive')
    )
    op.create_index(op.f('ix_batch_deductions_id'), 'batch_deductions', ['id'], unique=False)
    op.create_index('ix_batch_deductions_batch_id', 'batch_deductions', ['batch_id'], unique=False)
    op.create_index('ix_batch_deductions_daily_record_id', 'batch_deductions', ['daily_record_id'], unique=False)

    # =========================================================================
    # STEP 4: Add batch_id FK to spoilages
    # =========================================================================
    op.add_column('spoilages', sa.Column(
        'batch_id',
        sa.Integer(),
        sa.ForeignKey('ingredient_batches.id', ondelete='SET NULL'),
        nullable=True
    ))
    op.create_index('ix_spoilages_batch_id', 'spoilages', ['batch_id'], unique=False)


def downgrade() -> None:
    # =========================================================================
    # STEP 1: Remove batch_id from spoilages
    # =========================================================================
    op.drop_index('ix_spoilages_batch_id', 'spoilages')
    op.drop_constraint('spoilages_batch_id_fkey', 'spoilages', type_='foreignkey')
    op.drop_column('spoilages', 'batch_id')

    # =========================================================================
    # STEP 2: Drop batch_deductions table
    # =========================================================================
    op.drop_index('ix_batch_deductions_daily_record_id', 'batch_deductions')
    op.drop_index('ix_batch_deductions_batch_id', 'batch_deductions')
    op.drop_index(op.f('ix_batch_deductions_id'), 'batch_deductions')
    op.drop_table('batch_deductions')

    # =========================================================================
    # STEP 3: Drop ingredient_batches table
    # =========================================================================
    op.drop_index('ix_ingredient_batches_batch_number', 'ingredient_batches')
    op.drop_index('ix_ingredient_batches_expiry_date', 'ingredient_batches')
    op.drop_index('ix_ingredient_batches_ingredient_id', 'ingredient_batches')
    op.drop_index(op.f('ix_ingredient_batches_id'), 'ingredient_batches')
    op.drop_table('ingredient_batches')

    # =========================================================================
    # STEP 4: Remove expiry_date from delivery_items
    # =========================================================================
    op.drop_column('delivery_items', 'expiry_date')
