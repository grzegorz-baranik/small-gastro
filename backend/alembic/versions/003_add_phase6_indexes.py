"""Add Phase 6 performance indexes

Revision ID: 003
Revises: 002
Create Date: 2026-01-01

This migration adds performance indexes identified during Phase 6 optimization:
- Index on daily_records.date for frequent date filtering
- Compound index on inventory_snapshots for (daily_record_id, snapshot_type) queries
- Index on inventory_snapshots.daily_record_id
"""
from typing import Sequence, Union
from alembic import op


revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Index on daily_records.date for frequent filtering by date
    # Note: unique constraint may already create implicit index, but explicit is clearer
    op.create_index(
        'ix_daily_records_date',
        'daily_records',
        ['date'],
        unique=False
    )

    # Compound index on inventory_snapshots for efficient queries by record + type
    op.create_index(
        'ix_inventory_snapshots_record_type',
        'inventory_snapshots',
        ['daily_record_id', 'snapshot_type'],
        unique=False
    )

    # Simple index on inventory_snapshots.daily_record_id
    op.create_index(
        'ix_inventory_snapshots_daily_record_id',
        'inventory_snapshots',
        ['daily_record_id'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('ix_inventory_snapshots_daily_record_id', table_name='inventory_snapshots')
    op.drop_index('ix_inventory_snapshots_record_type', table_name='inventory_snapshots')
    op.drop_index('ix_daily_records_date', table_name='daily_records')
