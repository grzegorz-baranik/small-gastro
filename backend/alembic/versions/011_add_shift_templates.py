"""Add shift templates and schedule overrides

Revision ID: 011
Revises: 010
Create Date: 2026-01-06

This migration adds support for:
- Shift templates (recurring shift patterns for employees)
- Schedule overrides (date-specific schedule modifications or day-offs)

These tables support the Unified Day Operations feature's shift scheduling module.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '011'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # STEP 1: Create shift_templates table
    # =========================================================================
    op.create_table(
        'shift_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('day_of_week', sa.SmallInteger(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(
            ['employee_id'], ['employees.id'],
            name='fk_shift_templates_employee_id',
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('employee_id', 'day_of_week', name='unique_template_per_day'),
        sa.CheckConstraint('day_of_week >= 0 AND day_of_week <= 6', name='valid_day_of_week'),
        sa.CheckConstraint('end_time > start_time', name='template_valid_time_range'),
    )
    op.create_index(op.f('ix_shift_templates_id'), 'shift_templates', ['id'], unique=False)
    op.create_index('idx_shift_templates_employee', 'shift_templates', ['employee_id'], unique=False)
    op.create_index('idx_shift_templates_day', 'shift_templates', ['day_of_week'], unique=False)

    # =========================================================================
    # STEP 2: Create shift_schedule_overrides table
    # =========================================================================
    op.create_table(
        'shift_schedule_overrides',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=True),
        sa.Column('end_time', sa.Time(), nullable=True),
        sa.Column('is_day_off', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(
            ['employee_id'], ['employees.id'],
            name='fk_schedule_overrides_employee_id',
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('employee_id', 'date', name='unique_override_per_date'),
        sa.CheckConstraint(
            '(is_day_off = true) OR (start_time IS NOT NULL AND end_time IS NOT NULL AND end_time > start_time)',
            name='override_valid_times'
        ),
    )
    op.create_index(op.f('ix_shift_schedule_overrides_id'), 'shift_schedule_overrides', ['id'], unique=False)
    op.create_index('idx_schedule_overrides_employee', 'shift_schedule_overrides', ['employee_id'], unique=False)
    op.create_index('idx_schedule_overrides_date', 'shift_schedule_overrides', ['date'], unique=False)


def downgrade() -> None:
    # =========================================================================
    # STEP 1: Drop shift_schedule_overrides table
    # =========================================================================
    op.drop_index('idx_schedule_overrides_date', table_name='shift_schedule_overrides')
    op.drop_index('idx_schedule_overrides_employee', table_name='shift_schedule_overrides')
    op.drop_index(op.f('ix_shift_schedule_overrides_id'), table_name='shift_schedule_overrides')
    op.drop_table('shift_schedule_overrides')

    # =========================================================================
    # STEP 2: Drop shift_templates table
    # =========================================================================
    op.drop_index('idx_shift_templates_day', table_name='shift_templates')
    op.drop_index('idx_shift_templates_employee', table_name='shift_templates')
    op.drop_index(op.f('ix_shift_templates_id'), table_name='shift_templates')
    op.drop_table('shift_templates')
