from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from app.models.position import Position
from app.models.employee import Employee
from app.schemas.position import PositionCreate, PositionUpdate
from app.core.i18n import t


class PositionExistsError(Exception):
    """Raised when trying to create a position with a name that already exists."""
    pass


class PositionHasEmployeesError(Exception):
    """Raised when trying to delete a position that has employees assigned."""
    pass


class PositionNotFoundError(Exception):
    """Raised when a position is not found."""
    pass


def get_positions(db: Session) -> list[Position]:
    """
    Get all positions with employee counts.
    """
    return db.query(Position).order_by(Position.name).all()


def get_position(db: Session, position_id: int) -> Optional[Position]:
    """
    Get a position by ID.
    """
    return db.query(Position).filter(Position.id == position_id).first()


def get_position_with_employee_count(db: Session, position_id: int) -> tuple[Position, int]:
    """
    Get a position with its employee count.
    """
    position = get_position(db, position_id)
    if not position:
        return None, 0

    count = db.query(func.count(Employee.id)).filter(
        Employee.position_id == position_id
    ).scalar() or 0

    return position, count


def get_employee_count_for_position(db: Session, position_id: int) -> int:
    """
    Get the number of employees assigned to a position.
    """
    return db.query(func.count(Employee.id)).filter(
        Employee.position_id == position_id
    ).scalar() or 0


def create_position(db: Session, data: PositionCreate) -> Position:
    """
    Create a new position.
    Raises PositionExistsError if a position with the same name already exists.
    """
    # Check if position with this name already exists
    existing = db.query(Position).filter(
        func.lower(Position.name) == func.lower(data.name)
    ).first()

    if existing:
        raise PositionExistsError(t("errors.position_exists"))

    position = Position(
        name=data.name,
        hourly_rate=data.hourly_rate,
    )
    db.add(position)
    db.commit()
    db.refresh(position)

    return position


def update_position(db: Session, position_id: int, data: PositionUpdate) -> Position:
    """
    Update a position.
    Raises PositionNotFoundError if the position doesn't exist.
    Raises PositionExistsError if another position with the new name already exists.
    """
    position = get_position(db, position_id)
    if not position:
        raise PositionNotFoundError(t("errors.position_not_found"))

    update_data = data.model_dump(exclude_unset=True)

    # Check for name conflict if name is being updated
    if "name" in update_data and update_data["name"]:
        existing = db.query(Position).filter(
            func.lower(Position.name) == func.lower(update_data["name"]),
            Position.id != position_id
        ).first()

        if existing:
            raise PositionExistsError(t("errors.position_exists"))

    for field, value in update_data.items():
        setattr(position, field, value)

    db.commit()
    db.refresh(position)

    return position


def delete_position(db: Session, position_id: int) -> bool:
    """
    Delete a position.
    Raises PositionNotFoundError if the position doesn't exist.
    Raises PositionHasEmployeesError if the position has employees assigned.
    """
    position = get_position(db, position_id)
    if not position:
        raise PositionNotFoundError(t("errors.position_not_found"))

    # Check if any employees are assigned to this position
    employee_count = get_employee_count_for_position(db, position_id)
    if employee_count > 0:
        raise PositionHasEmployeesError(t("errors.position_has_employees"))

    db.delete(position)
    db.commit()

    return True
