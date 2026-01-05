from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional
from app.models.employee import Employee
from app.models.position import Position
from app.models.shift_assignment import ShiftAssignment
from app.models.transaction import Transaction
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.core.i18n import t


class EmployeeNotFoundError(Exception):
    """Raised when an employee is not found."""
    pass


class PositionNotFoundError(Exception):
    """Raised when a position is not found."""
    pass


class EmployeeHasHistoryError(Exception):
    """Raised when trying to delete an employee with shift/wage history."""
    pass


def get_employees(
    db: Session,
    include_inactive: bool = False,
) -> list[Employee]:
    """
    Get all employees with position data.
    By default only returns active employees.
    """
    query = db.query(Employee).options(joinedload(Employee.position))

    if not include_inactive:
        query = query.filter(Employee.is_active == True)

    return query.order_by(Employee.name).all()


def get_employee(db: Session, employee_id: int) -> Optional[Employee]:
    """
    Get an employee by ID with position data.
    """
    return (
        db.query(Employee)
        .options(joinedload(Employee.position))
        .filter(Employee.id == employee_id)
        .first()
    )


def create_employee(db: Session, data: EmployeeCreate) -> Employee:
    """
    Create a new employee.
    Raises PositionNotFoundError if the position doesn't exist.
    """
    # Verify position exists
    position = db.query(Position).filter(Position.id == data.position_id).first()
    if not position:
        raise PositionNotFoundError(t("errors.position_not_found"))

    employee = Employee(
        name=data.name,
        position_id=data.position_id,
        hourly_rate_override=data.hourly_rate,
        is_active=data.is_active,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)

    # Re-fetch with position loaded
    return get_employee(db, employee.id)


def update_employee(db: Session, employee_id: int, data: EmployeeUpdate) -> Employee:
    """
    Update an employee.
    Raises EmployeeNotFoundError if the employee doesn't exist.
    Raises PositionNotFoundError if the new position doesn't exist.
    """
    employee = get_employee(db, employee_id)
    if not employee:
        raise EmployeeNotFoundError(t("errors.employee_not_found"))

    update_data = data.model_dump(exclude_unset=True)

    # Verify new position exists if being updated
    if "position_id" in update_data and update_data["position_id"]:
        position = db.query(Position).filter(
            Position.id == update_data["position_id"]
        ).first()
        if not position:
            raise PositionNotFoundError(t("errors.position_not_found"))

    # Map hourly_rate to hourly_rate_override in the model
    if "hourly_rate" in update_data:
        update_data["hourly_rate_override"] = update_data.pop("hourly_rate")

    for field, value in update_data.items():
        setattr(employee, field, value)

    db.commit()

    # Re-fetch with position loaded
    return get_employee(db, employee_id)


def deactivate_employee(db: Session, employee_id: int) -> Employee:
    """
    Deactivate an employee (soft delete).
    Raises EmployeeNotFoundError if the employee doesn't exist.
    """
    employee = get_employee(db, employee_id)
    if not employee:
        raise EmployeeNotFoundError(t("errors.employee_not_found"))

    employee.is_active = False
    db.commit()

    return get_employee(db, employee_id)


def activate_employee(db: Session, employee_id: int) -> Employee:
    """
    Reactivate an employee.
    Raises EmployeeNotFoundError if the employee doesn't exist.
    """
    employee = get_employee(db, employee_id)
    if not employee:
        raise EmployeeNotFoundError(t("errors.employee_not_found"))

    employee.is_active = True
    db.commit()

    return get_employee(db, employee_id)


def delete_employee(db: Session, employee_id: int) -> bool:
    """
    Delete an employee permanently.
    Raises EmployeeNotFoundError if the employee doesn't exist.
    Raises EmployeeHasHistoryError if the employee has shift or wage history.
    """
    employee = get_employee(db, employee_id)
    if not employee:
        raise EmployeeNotFoundError(t("errors.employee_not_found"))

    # Check for shift history
    shift_count = db.query(func.count(ShiftAssignment.id)).filter(
        ShiftAssignment.employee_id == employee_id
    ).scalar() or 0

    if shift_count > 0:
        raise EmployeeHasHistoryError(t("errors.employee_has_shifts"))

    # Check for wage transactions
    wage_count = db.query(func.count(Transaction.id)).filter(
        Transaction.employee_id == employee_id
    ).scalar() or 0

    if wage_count > 0:
        raise EmployeeHasHistoryError(t("errors.employee_has_wages"))

    db.delete(employee)
    db.commit()

    return True


def count_employees(db: Session, include_inactive: bool = False) -> int:
    """
    Count total number of employees.
    """
    query = db.query(func.count(Employee.id))
    if not include_inactive:
        query = query.filter(Employee.is_active == True)
    return query.scalar() or 0
