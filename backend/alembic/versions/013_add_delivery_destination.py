"""Add destination field to deliveries table

Revision ID: 013
Revises: 012
Create Date: 2026-01-06

This migration adds the destination column to the deliveries table to support
choosing whether a delivery goes to warehouse (storage) or shop.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '013'
down_revision: Union[str, None] = '012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # Add destination column to deliveries table
    # Uses existing batchlocation enum type if available, otherwise VARCHAR
    # Default value is 'storage' for backwards compatibility
    # =========================================================================

    # Add column with default value
    op.add_column(
        'deliveries',
        sa.Column(
            'destination',
            sa.String(20),
            nullable=False,
            server_default='storage'
        )
    )

    # Add check constraint to ensure valid values
    op.create_check_constraint(
        'check_delivery_destination_valid',
        'deliveries',
        "destination IN ('storage', 'shop')"
    )


def downgrade() -> None:
    # =========================================================================
    # Remove destination column from deliveries table
    # =========================================================================

    # Drop check constraint first
    op.drop_constraint('check_delivery_destination_valid', 'deliveries', type_='check')

    # Drop the column
    op.drop_column('deliveries', 'destination')
