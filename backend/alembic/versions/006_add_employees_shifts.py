"""Add employees and shifts management

Revision ID: 006
Revises: 005
Create Date: 2026-01-04

This migration adds support for:
- Positions (job roles with default hourly rates)
- Employees (workers assigned to positions)
- Shift assignments (linking employees to daily records with work times)
- Wage tracking in transactions (employee_id, period type, dates)

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # STEP 1: Create wage_period_type enum
    # =========================================================================
    wage_period_type_enum = postgresql.ENUM(
        'daily', 'weekly', 'biweekly', 'monthly',
        name='wageperiodtype',
        create_type=False
    )
    wage_period_type_enum.create(op.get_bind(), checkfirst=True)

    # =========================================================================
    # STEP 2: Create positions table
    # =========================================================================
    op.create_table(
        'positions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('hourly_rate', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_positions_name')
    )
    op.create_index(op.f('ix_positions_id'), 'positions', ['id'], unique=False)

    # =========================================================================
    # STEP 3: Create employees table
    # =========================================================================
    op.create_table(
        'employees',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('position_id', sa.Integer(), nullable=False),
        sa.Column('hourly_rate_override', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['position_id'], ['positions.id'], name='fk_employees_position_id'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_employees_id'), 'employees', ['id'], unique=False)
    op.create_index('idx_employees_position', 'employees', ['position_id'], unique=False)
    op.create_index('idx_employees_active', 'employees', ['is_active'], unique=False)

    # =========================================================================
    # STEP 4: Create shift_assignments table
    # =========================================================================
    op.create_table(
        'shift_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('daily_record_id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['daily_record_id'], ['daily_records.id'], name='fk_shift_assignments_daily_record_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], name='fk_shift_assignments_employee_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('daily_record_id', 'employee_id', name='unique_employee_per_day'),
        sa.CheckConstraint('end_time > start_time', name='valid_time_range')
    )
    op.create_index(op.f('ix_shift_assignments_id'), 'shift_assignments', ['id'], unique=False)
    op.create_index('idx_shift_assignments_daily_record', 'shift_assignments', ['daily_record_id'], unique=False)
    op.create_index('idx_shift_assignments_employee', 'shift_assignments', ['employee_id'], unique=False)

    # =========================================================================
    # STEP 5: Add wage-specific columns to transactions table
    # =========================================================================
    op.add_column('transactions', sa.Column('employee_id', sa.Integer(), nullable=True))
    op.add_column('transactions', sa.Column(
        'wage_period_type',
        postgresql.ENUM('daily', 'weekly', 'biweekly', 'monthly', name='wageperiodtype', create_type=False),
        nullable=True
    ))
    op.add_column('transactions', sa.Column('wage_period_start', sa.Date(), nullable=True))
    op.add_column('transactions', sa.Column('wage_period_end', sa.Date(), nullable=True))

    # Add FK constraint for employee_id
    op.create_foreign_key(
        'fk_transactions_employee_id',
        'transactions',
        'employees',
        ['employee_id'],
        ['id']
    )

    # Add index for employee_id
    op.create_index('idx_transactions_employee', 'transactions', ['employee_id'], unique=False)


def downgrade() -> None:
    # =========================================================================
    # STEP 1: Remove wage-specific columns from transactions
    # =========================================================================
    op.drop_index('idx_transactions_employee', table_name='transactions')
    op.drop_constraint('fk_transactions_employee_id', 'transactions', type_='foreignkey')
    op.drop_column('transactions', 'wage_period_end')
    op.drop_column('transactions', 'wage_period_start')
    op.drop_column('transactions', 'wage_period_type')
    op.drop_column('transactions', 'employee_id')

    # =========================================================================
    # STEP 2: Drop shift_assignments table
    # =========================================================================
    op.drop_index('idx_shift_assignments_employee', table_name='shift_assignments')
    op.drop_index('idx_shift_assignments_daily_record', table_name='shift_assignments')
    op.drop_index(op.f('ix_shift_assignments_id'), table_name='shift_assignments')
    op.drop_table('shift_assignments')

    # =========================================================================
    # STEP 3: Drop employees table
    # =========================================================================
    op.drop_index('idx_employees_active', table_name='employees')
    op.drop_index('idx_employees_position', table_name='employees')
    op.drop_index(op.f('ix_employees_id'), table_name='employees')
    op.drop_table('employees')

    # =========================================================================
    # STEP 4: Drop positions table
    # =========================================================================
    op.drop_index(op.f('ix_positions_id'), table_name='positions')
    op.drop_table('positions')

    # =========================================================================
    # STEP 5: Drop wage_period_type enum
    # =========================================================================
    op.execute('DROP TYPE IF EXISTS wageperiodtype')
