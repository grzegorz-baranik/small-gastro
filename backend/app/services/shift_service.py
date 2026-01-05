from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from typing import Optional
from datetime import date, time
from app.models.shift_assignment import ShiftAssignment
from app.models.employee import Employee
from app.models.daily_record import DailyRecord, DayStatus
from app.schemas.shift_assignment import ShiftAssignmentCreate, ShiftAssignmentUpdate
from app.core.i18n import t


class ShiftNotFoundError(Exception):
    """Raised when a shift assignment is not found."""
    pass


class DailyRecordNotFoundError(Exception):
    """Raised when a daily record is not found."""
    pass


class DayNotOpenError(Exception):
    """Raised when trying to modify shifts on a closed day."""
    pass


class EmployeeNotFoundError(Exception):
    """Raised when an employee is not found."""
    pass


class EmployeeAlreadyAssignedError(Exception):
    """Raised when an employee is already assigned to the day."""
    pass


class InvalidTimeRangeError(Exception):
    """Raised when end time is not after start time."""
    pass


def get_shifts_by_daily_record(db: Session, daily_record_id: int) -> list[ShiftAssignment]:
    """
    Get all shift assignments for a daily record with employee data.
    """
    return (
        db.query(ShiftAssignment)
        .options(joinedload(ShiftAssignment.employee).joinedload(Employee.position))
        .filter(ShiftAssignment.daily_record_id == daily_record_id)
        .order_by(ShiftAssignment.start_time)
        .all()
    )


def get_shift(db: Session, shift_id: int) -> Optional[ShiftAssignment]:
    """
    Get a shift assignment by ID with employee data.
    """
    return (
        db.query(ShiftAssignment)
        .options(joinedload(ShiftAssignment.employee).joinedload(Employee.position))
        .filter(ShiftAssignment.id == shift_id)
        .first()
    )


def _validate_daily_record_open(db: Session, daily_record_id: int) -> DailyRecord:
    """
    Validate that the daily record exists and is open.
    Returns the daily record if valid.
    """
    daily_record = db.query(DailyRecord).filter(
        DailyRecord.id == daily_record_id
    ).first()

    if not daily_record:
        raise DailyRecordNotFoundError(t("errors.daily_record_not_found"))

    if daily_record.status != DayStatus.OPEN:
        raise DayNotOpenError(t("errors.cannot_add_to_closed_day"))

    return daily_record


def _validate_employee_exists(db: Session, employee_id: int) -> Employee:
    """
    Validate that the employee exists.
    Returns the employee if valid.
    """
    employee = db.query(Employee).filter(
        Employee.id == employee_id
    ).first()

    if not employee:
        raise EmployeeNotFoundError(t("errors.employee_not_found"))

    return employee


def create_shift(
    db: Session,
    daily_record_id: int,
    data: ShiftAssignmentCreate,
) -> ShiftAssignment:
    """
    Create a new shift assignment.
    Validates that the day is open and the employee exists.
    """
    # Validate day is open
    _validate_daily_record_open(db, daily_record_id)

    # Validate employee exists
    _validate_employee_exists(db, data.employee_id)

    # Validate time range
    if data.end_time <= data.start_time:
        raise InvalidTimeRangeError(t("errors.shift_end_before_start"))

    shift = ShiftAssignment(
        daily_record_id=daily_record_id,
        employee_id=data.employee_id,
        start_time=data.start_time,
        end_time=data.end_time,
    )

    try:
        db.add(shift)
        db.commit()
        db.refresh(shift)
    except IntegrityError:
        db.rollback()
        raise EmployeeAlreadyAssignedError(t("errors.employee_already_assigned"))

    # Re-fetch with relationships loaded
    return get_shift(db, shift.id)


def update_shift(
    db: Session,
    daily_record_id: int,
    shift_id: int,
    data: ShiftAssignmentUpdate,
) -> ShiftAssignment:
    """
    Update shift times.
    Validates that the day is open.
    """
    # Validate day is open
    _validate_daily_record_open(db, daily_record_id)

    shift = get_shift(db, shift_id)
    if not shift:
        raise ShiftNotFoundError(t("errors.shift_not_found"))

    # Verify the shift belongs to the specified daily record
    if shift.daily_record_id != daily_record_id:
        raise ShiftNotFoundError(t("errors.shift_not_found"))

    # Validate time range
    if data.end_time <= data.start_time:
        raise InvalidTimeRangeError(t("errors.shift_end_before_start"))

    shift.start_time = data.start_time
    shift.end_time = data.end_time

    db.commit()

    return get_shift(db, shift_id)


def delete_shift(db: Session, daily_record_id: int, shift_id: int) -> bool:
    """
    Delete a shift assignment.
    Validates that the day is open.
    """
    # Validate day is open
    _validate_daily_record_open(db, daily_record_id)

    shift = get_shift(db, shift_id)
    if not shift:
        raise ShiftNotFoundError(t("errors.shift_not_found"))

    # Verify the shift belongs to the specified daily record
    if shift.daily_record_id != daily_record_id:
        raise ShiftNotFoundError(t("errors.shift_not_found"))

    db.delete(shift)
    db.commit()

    return True


def count_shifts_for_day(db: Session, daily_record_id: int) -> int:
    """
    Count the number of employees assigned for a day.
    """
    return db.query(func.count(ShiftAssignment.id)).filter(
        ShiftAssignment.daily_record_id == daily_record_id
    ).scalar() or 0


def validate_minimum_employees(db: Session, daily_record_id: int) -> bool:
    """
    Check if at least one employee is assigned to the day.
    """
    return count_shifts_for_day(db, daily_record_id) >= 1


def calculate_hours_for_period(
    db: Session,
    employee_id: int,
    start_date: date,
    end_date: date,
) -> float:
    """
    Calculate total hours worked by an employee in a date range.
    """
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
