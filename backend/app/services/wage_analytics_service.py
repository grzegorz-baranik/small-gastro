from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, extract
from typing import Optional
from datetime import date
from decimal import Decimal
from calendar import monthrange
from app.models.employee import Employee
from app.models.position import Position
from app.models.shift_assignment import ShiftAssignment
from app.models.daily_record import DailyRecord
from app.models.transaction import Transaction, TransactionType
from app.schemas.wage_analytics import WageAnalyticsResponse, WageSummary, EmployeeWageStats, HoursCalculationResponse


def _get_month_date_range(month: int, year: int) -> tuple[date, date]:
    """
    Get the first and last day of a month.
    """
    first_day = date(year, month, 1)
    _, last_day_num = monthrange(year, month)
    last_day = date(year, month, last_day_num)
    return first_day, last_day


def _get_previous_month(month: int, year: int) -> tuple[int, int]:
    """
    Get the previous month and year.
    """
    if month == 1:
        return 12, year - 1
    return month - 1, year


def get_employee_hours_for_month(
    db: Session,
    employee_id: int,
    month: int,
    year: int,
) -> float:
    """
    Get total hours worked by an employee in a month.
    """
    start_date, end_date = _get_month_date_range(month, year)

    shifts = (
        db.query(ShiftAssignment)
        .join(DailyRecord)
        .filter(
            ShiftAssignment.employee_id == employee_id,
            DailyRecord.date >= start_date,
            DailyRecord.date <= end_date,
        )
        .all()
    )

    return sum(shift.hours_worked for shift in shifts)


def get_employee_hours_for_period(
    db: Session,
    employee_id: int,
    start_date: date,
    end_date: date,
) -> HoursCalculationResponse:
    """
    Get total hours worked by an employee in a date range
    and calculate the wage based on their hourly rate.
    """
    from app.services.employee_service import get_employee

    employee = get_employee(db, employee_id)
    if not employee:
        raise ValueError(f"Employee with ID {employee_id} not found")

    shifts = (
        db.query(ShiftAssignment)
        .join(DailyRecord)
        .filter(
            ShiftAssignment.employee_id == employee_id,
            DailyRecord.date >= start_date,
            DailyRecord.date <= end_date,
        )
        .all()
    )

    total_hours = sum(shift.hours_worked for shift in shifts)
    hourly_rate = employee.effective_hourly_rate
    calculated_wage = Decimal(str(total_hours)) * hourly_rate

    return HoursCalculationResponse(
        employee_id=employee_id,
        hours=total_hours,
        calculated_wage=calculated_wage.quantize(Decimal("0.01")),
    )


def get_employee_wages_for_month(
    db: Session,
    employee_id: int,
    month: int,
    year: int,
) -> Decimal:
    """
    Get total wages paid to an employee in a month.
    Wages are expense transactions with employee_id set.
    """
    start_date, end_date = _get_month_date_range(month, year)

    total = db.query(func.sum(Transaction.amount)).filter(
        Transaction.employee_id == employee_id,
        Transaction.type == TransactionType.EXPENSE,
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date,
    ).scalar()

    return Decimal(str(total)) if total else Decimal("0")


def _get_summary_for_month(
    db: Session,
    month: int,
    year: int,
    employee_id: Optional[int] = None,
) -> WageSummary:
    """
    Get wage summary for a specific month.
    """
    start_date, end_date = _get_month_date_range(month, year)

    # Build base query for wage transactions
    wage_query = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == TransactionType.EXPENSE,
        Transaction.employee_id.isnot(None),
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date,
    )

    if employee_id:
        wage_query = wage_query.filter(Transaction.employee_id == employee_id)

    total_wages = wage_query.scalar() or Decimal("0")
    total_wages = Decimal(str(total_wages))

    # Calculate total hours from shifts
    shift_query = (
        db.query(ShiftAssignment)
        .join(DailyRecord)
        .filter(
            DailyRecord.date >= start_date,
            DailyRecord.date <= end_date,
        )
    )

    if employee_id:
        shift_query = shift_query.filter(ShiftAssignment.employee_id == employee_id)

    shifts = shift_query.all()
    total_hours = sum(shift.hours_worked for shift in shifts)

    # Calculate average cost per hour
    avg_cost = Decimal("0")
    if total_hours > 0:
        avg_cost = total_wages / Decimal(str(total_hours))

    return WageSummary(
        total_wages=total_wages,
        total_hours=total_hours,
        avg_cost_per_hour=avg_cost.quantize(Decimal("0.01")),
    )


def _get_employee_stats(
    db: Session,
    employee: Employee,
    month: int,
    year: int,
) -> EmployeeWageStats:
    """
    Get wage statistics for a single employee.
    """
    # Get current month data
    hours_worked = get_employee_hours_for_month(db, employee.id, month, year)
    wages_paid = get_employee_wages_for_month(db, employee.id, month, year)

    # Calculate cost per hour
    cost_per_hour = Decimal("0")
    if hours_worked > 0:
        cost_per_hour = wages_paid / Decimal(str(hours_worked))

    # Get previous month data for comparison
    prev_month, prev_year = _get_previous_month(month, year)
    prev_wages = get_employee_wages_for_month(db, employee.id, prev_month, prev_year)

    # Calculate change percentage
    change_percent = None
    if prev_wages > 0:
        change = ((wages_paid - prev_wages) / prev_wages) * 100
        change_percent = float(change.quantize(Decimal("0.1")))

    return EmployeeWageStats(
        employee_id=employee.id,
        employee_name=employee.name,
        position_name=employee.position.name if employee.position else "",
        hours_worked=hours_worked,
        wages_paid=wages_paid,
        cost_per_hour=cost_per_hour.quantize(Decimal("0.01")),
        previous_month_wages=prev_wages if prev_wages > 0 else None,
        change_percent=change_percent,
    )


def get_wage_analytics(
    db: Session,
    month: int,
    year: int,
    employee_id: Optional[int] = None,
) -> WageAnalyticsResponse:
    """
    Get comprehensive wage analytics for a month.
    Includes summary and per-employee breakdown.
    """
    # Get current month summary
    summary = _get_summary_for_month(db, month, year, employee_id)

    # Get previous month summary
    prev_month, prev_year = _get_previous_month(month, year)
    prev_summary = _get_summary_for_month(db, prev_month, prev_year, employee_id)

    # Only include previous month summary if there was any activity
    if prev_summary.total_wages == 0 and prev_summary.total_hours == 0:
        prev_summary = None

    # Get per-employee breakdown
    by_employee = []

    if employee_id:
        # Single employee mode
        employee = (
            db.query(Employee)
            .options(joinedload(Employee.position))
            .filter(Employee.id == employee_id)
            .first()
        )
        if employee:
            by_employee.append(_get_employee_stats(db, employee, month, year))
    else:
        # All employees who had shifts or wages in the period
        start_date, end_date = _get_month_date_range(month, year)

        # Get employees with shifts in the period
        employees_with_shifts = (
            db.query(Employee)
            .options(joinedload(Employee.position))
            .join(ShiftAssignment)
            .join(DailyRecord)
            .filter(
                DailyRecord.date >= start_date,
                DailyRecord.date <= end_date,
            )
            .distinct()
            .all()
        )

        # Get employees with wage transactions in the period
        employees_with_wages = (
            db.query(Employee)
            .options(joinedload(Employee.position))
            .join(Transaction)
            .filter(
                Transaction.type == TransactionType.EXPENSE,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
            )
            .distinct()
            .all()
        )

        # Combine and deduplicate
        employee_ids_seen = set()
        all_employees = []

        for emp in employees_with_shifts + employees_with_wages:
            if emp.id not in employee_ids_seen:
                employee_ids_seen.add(emp.id)
                all_employees.append(emp)

        # Sort by name
        all_employees.sort(key=lambda e: e.name)

        for employee in all_employees:
            by_employee.append(_get_employee_stats(db, employee, month, year))

    return WageAnalyticsResponse(
        summary=summary,
        previous_month_summary=prev_summary,
        by_employee=by_employee,
    )
