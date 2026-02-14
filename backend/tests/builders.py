"""
Test data builders for creating test fixtures.

Builders create database objects with sensible defaults that can be overridden.
Use these directly in tests instead of creating fixture wrappers.

Usage:
    user = build_ingredient(db_session, name="Cebula", unit_type=UnitType.WEIGHT)
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.ingredient import Ingredient, UnitType
from app.models.daily_record import DailyRecord, DayStatus
from app.models.inventory_snapshot import InventorySnapshot, SnapshotType, InventoryLocation
from app.models.transaction import Transaction, TransactionType, PaymentMethod
from app.models.expense_category import ExpenseCategory
from app.models.spoilage import Spoilage, SpoilageReason
from app.models.delivery import Delivery
from app.models.storage_transfer import StorageTransfer
from app.models.position import Position
from app.models.employee import Employee
from app.models.shift_assignment import ShiftAssignment
from app.models.transaction import WagePeriodType


def build_ingredient(
    db: Session,
    name: Optional[str] = None,
    unit_type: UnitType = UnitType.WEIGHT,
    unit_label: str = "kg",
    is_active: bool = True,
    **overrides
) -> Ingredient:
    """Create an ingredient with sensible defaults."""
    # Generate unique name if not provided
    if name is None:
        # Count existing ingredients for unique naming
        count = db.query(Ingredient).count()
        name = f"Test Ingredient {count + 1}"

    data = {
        "name": name,
        "unit_type": unit_type,
        "unit_label": unit_label,
        "is_active": is_active,
    }
    data.update(overrides)

    ingredient = Ingredient(**data)
    db.add(ingredient)
    db.flush()
    return ingredient


def build_expense_category(
    db: Session,
    name: Optional[str] = None,
    parent_id: Optional[int] = None,
    level: int = 1,
    is_active: bool = True,
    **overrides
) -> ExpenseCategory:
    """Create an expense category with sensible defaults."""
    if name is None:
        count = db.query(ExpenseCategory).count()
        name = f"Test Category {count + 1}"

    data = {
        "name": name,
        "parent_id": parent_id,
        "level": level,
        "is_active": is_active,
    }
    data.update(overrides)

    category = ExpenseCategory(**data)
    db.add(category)
    db.flush()
    return category


def build_daily_record(
    db: Session,
    record_date: Optional[date] = None,
    status: DayStatus = DayStatus.OPEN,
    opened_at: Optional[datetime] = None,
    closed_at: Optional[datetime] = None,
    total_income_pln: Optional[Decimal] = None,
    total_delivery_cost_pln: Decimal = Decimal("0"),
    total_spoilage_cost_pln: Decimal = Decimal("0"),
    notes: Optional[str] = None,
    **overrides
) -> DailyRecord:
    """Create a daily record with sensible defaults."""
    if record_date is None:
        record_date = date.today()
    if opened_at is None:
        opened_at = datetime.now()
    if status == DayStatus.CLOSED and closed_at is None:
        closed_at = datetime.now()

    data = {
        "date": record_date,
        "status": status,
        "opened_at": opened_at,
        "closed_at": closed_at,
        "total_income_pln": total_income_pln,
        "total_delivery_cost_pln": total_delivery_cost_pln,
        "total_spoilage_cost_pln": total_spoilage_cost_pln,
        "notes": notes,
    }
    data.update(overrides)

    record = DailyRecord(**data)
    db.add(record)
    db.flush()
    return record


def build_inventory_snapshot(
    db: Session,
    daily_record_id: int,
    ingredient_id: int,
    snapshot_type: SnapshotType = SnapshotType.OPEN,
    location: InventoryLocation = InventoryLocation.SHOP,
    quantity: Decimal = Decimal("10.00"),
    **overrides
) -> InventorySnapshot:
    """Create an inventory snapshot with sensible defaults."""
    data = {
        "daily_record_id": daily_record_id,
        "ingredient_id": ingredient_id,
        "snapshot_type": snapshot_type,
        "location": location,
        "quantity": quantity,
    }
    data.update(overrides)

    snapshot = InventorySnapshot(**data)
    db.add(snapshot)
    db.flush()
    return snapshot


def build_transaction(
    db: Session,
    transaction_type: TransactionType = TransactionType.EXPENSE,
    amount: Decimal = Decimal("100.00"),
    payment_method: PaymentMethod = PaymentMethod.CASH,
    transaction_date: Optional[date] = None,
    category_id: Optional[int] = None,
    daily_record_id: Optional[int] = None,
    description: Optional[str] = None,
    **overrides
) -> Transaction:
    """Create a transaction with sensible defaults."""
    if transaction_date is None:
        transaction_date = date.today()

    data = {
        "type": transaction_type,
        "amount": amount,
        "payment_method": payment_method,
        "transaction_date": transaction_date,
        "category_id": category_id,
        "daily_record_id": daily_record_id,
        "description": description,
    }
    data.update(overrides)

    transaction = Transaction(**data)
    db.add(transaction)
    db.flush()
    return transaction


def build_spoilage(
    db: Session,
    daily_record_id: int,
    ingredient_id: int,
    quantity: Decimal = Decimal("1.00"),
    reason: SpoilageReason = SpoilageReason.EXPIRED,
    notes: Optional[str] = None,
    **overrides
) -> Spoilage:
    """Create a spoilage record with sensible defaults."""
    data = {
        "daily_record_id": daily_record_id,
        "ingredient_id": ingredient_id,
        "quantity": quantity,
        "reason": reason,
        "notes": notes,
    }
    data.update(overrides)

    spoilage = Spoilage(**data)
    db.add(spoilage)
    db.flush()
    return spoilage


def build_delivery(
    db: Session,
    daily_record_id: int,
    ingredient_id: int,
    quantity: Decimal = Decimal("5.00"),
    price_pln: Decimal = Decimal("50.00"),
    supplier_name: Optional[str] = None,
    **overrides
) -> Delivery:
    """
    Create a delivery record with a single item.

    Note: The Delivery model now uses DeliveryItem for ingredients.
    This builder creates a Delivery with one DeliveryItem for convenience.
    """
    from app.models.delivery import DeliveryItem

    # Create the delivery
    delivery_data = {
        "daily_record_id": daily_record_id,
        "total_cost_pln": price_pln,
        "supplier_name": supplier_name,
    }
    delivery_data.update(overrides)

    delivery = Delivery(**delivery_data)
    db.add(delivery)
    db.flush()

    # Create the delivery item
    item = DeliveryItem(
        delivery_id=delivery.id,
        ingredient_id=ingredient_id,
        quantity=quantity,
        cost_pln=price_pln,
    )
    db.add(item)
    db.flush()

    return delivery


def build_storage_transfer(
    db: Session,
    daily_record_id: int,
    ingredient_id: int,
    quantity: Decimal = Decimal("5.00"),
    transferred_at: Optional[datetime] = None,
    **overrides
) -> StorageTransfer:
    """Create a storage transfer record with sensible defaults."""
    if transferred_at is None:
        transferred_at = datetime.now()

    data = {
        "daily_record_id": daily_record_id,
        "ingredient_id": ingredient_id,
        "quantity": quantity,
        "transferred_at": transferred_at,
    }
    data.update(overrides)

    transfer = StorageTransfer(**data)
    db.add(transfer)
    db.flush()
    return transfer


def build_position(
    db: Session,
    name: Optional[str] = None,
    hourly_rate: Decimal = Decimal("25.00"),
    **overrides
) -> Position:
    """Create a position with sensible defaults."""
    if name is None:
        count = db.query(Position).count()
        name = f"Test Position {count + 1}"

    data = {
        "name": name,
        "hourly_rate": hourly_rate,
    }
    data.update(overrides)

    position = Position(**data)
    db.add(position)
    db.flush()
    return position


def build_employee(
    db: Session,
    name: Optional[str] = None,
    position_id: Optional[int] = None,
    position: Optional[Position] = None,
    hourly_rate_override: Optional[Decimal] = None,
    is_active: bool = True,
    **overrides
) -> Employee:
    """
    Create an employee with sensible defaults.

    You can pass either position_id or position object.
    If neither is provided, a new position will be created.
    """
    if name is None:
        count = db.query(Employee).count()
        name = f"Test Employee {count + 1}"

    # Handle position - use provided id, or get from object, or create new
    if position_id is None:
        if position is not None:
            position_id = position.id
        else:
            # Create a position for this employee
            new_position = build_position(db)
            position_id = new_position.id

    data = {
        "name": name,
        "position_id": position_id,
        "hourly_rate_override": hourly_rate_override,
        "is_active": is_active,
    }
    data.update(overrides)

    employee = Employee(**data)
    db.add(employee)
    db.flush()
    return employee


def build_shift_assignment(
    db: Session,
    daily_record_id: Optional[int] = None,
    daily_record: Optional[DailyRecord] = None,
    employee_id: Optional[int] = None,
    employee: Optional[Employee] = None,
    start_time: Optional["time"] = None,
    end_time: Optional["time"] = None,
    **overrides
) -> ShiftAssignment:
    """
    Create a shift assignment with sensible defaults.

    You can pass either daily_record_id/employee_id or the objects themselves.
    If not provided, will create new objects.
    """
    from datetime import time

    # Handle daily_record
    if daily_record_id is None:
        if daily_record is not None:
            daily_record_id = daily_record.id
        else:
            new_record = build_daily_record(db, status=DayStatus.OPEN)
            daily_record_id = new_record.id

    # Handle employee
    if employee_id is None:
        if employee is not None:
            employee_id = employee.id
        else:
            new_employee = build_employee(db)
            employee_id = new_employee.id

    # Default times
    if start_time is None:
        start_time = time(8, 0)
    if end_time is None:
        end_time = time(16, 0)

    data = {
        "daily_record_id": daily_record_id,
        "employee_id": employee_id,
        "start_time": start_time,
        "end_time": end_time,
    }
    data.update(overrides)

    shift = ShiftAssignment(**data)
    db.add(shift)
    db.flush()
    return shift


def build_wage_transaction(
    db: Session,
    employee_id: int,
    amount: Decimal = Decimal("1000.00"),
    transaction_date: Optional[date] = None,
    wage_period_type: WagePeriodType = WagePeriodType.MONTHLY,
    wage_period_start: Optional[date] = None,
    wage_period_end: Optional[date] = None,
    category_id: Optional[int] = None,
    **overrides
) -> Transaction:
    """Create a wage transaction (expense for an employee)."""
    if transaction_date is None:
        transaction_date = date.today()

    data = {
        "type": TransactionType.EXPENSE,
        "amount": amount,
        "payment_method": PaymentMethod.BANK_TRANSFER,
        "transaction_date": transaction_date,
        "employee_id": employee_id,
        "wage_period_type": wage_period_type,
        "wage_period_start": wage_period_start,
        "wage_period_end": wage_period_end,
        "category_id": category_id,
        "description": "Wyplata",
    }
    data.update(overrides)

    transaction = Transaction(**data)
    db.add(transaction)
    db.flush()
    return transaction


# -----------------------------------------------------------------------------
# Shift Template and Schedule Override Builders
# These builders are for the Unified Day Operations feature.
# Note: Models are expected to be created at:
#   - app/models/shift_template.py
#   - app/models/shift_schedule_override.py
# -----------------------------------------------------------------------------

def build_shift_template(
    db: Session,
    employee_id: Optional[int] = None,
    employee: Optional[Employee] = None,
    day_of_week: int = 0,  # 0=Monday, 6=Sunday
    start_time: Optional["time"] = None,
    end_time: Optional["time"] = None,
    **overrides
) -> "ShiftTemplate":
    """
    Create a shift template with sensible defaults.

    A shift template defines a recurring pattern for an employee's shifts
    (e.g., "Anna works Mon-Fri 08:00-16:00").

    You can pass either employee_id or employee object.
    If neither is provided, a new employee will be created.
    """
    from datetime import time as time_type
    # Import the model - this will fail until the model is created
    from app.models.shift_template import ShiftTemplate

    # Handle employee
    if employee_id is None:
        if employee is not None:
            employee_id = employee.id
        else:
            new_employee = build_employee(db)
            employee_id = new_employee.id

    # Default times
    if start_time is None:
        start_time = time_type(8, 0)
    if end_time is None:
        end_time = time_type(16, 0)

    data = {
        "employee_id": employee_id,
        "day_of_week": day_of_week,
        "start_time": start_time,
        "end_time": end_time,
    }
    data.update(overrides)

    template = ShiftTemplate(**data)
    db.add(template)
    db.flush()
    return template


def build_schedule_override(
    db: Session,
    employee_id: Optional[int] = None,
    employee: Optional[Employee] = None,
    override_date: Optional[date] = None,
    start_time: Optional["time"] = None,
    end_time: Optional["time"] = None,
    is_day_off: bool = False,
    **overrides
) -> "ShiftScheduleOverride":
    """
    Create a shift schedule override with sensible defaults.

    A schedule override replaces the template for a specific date.
    Can be used to:
    - Change shift hours for a specific day
    - Mark an employee as having the day off

    You can pass either employee_id or employee object.
    If neither is provided, a new employee will be created.
    """
    from datetime import time as time_type
    # Import the model - this will fail until the model is created
    from app.models.shift_schedule_override import ShiftScheduleOverride

    # Handle employee
    if employee_id is None:
        if employee is not None:
            employee_id = employee.id
        else:
            new_employee = build_employee(db)
            employee_id = new_employee.id

    # Default date
    if override_date is None:
        override_date = date.today()

    # Default times (unless day off)
    if not is_day_off:
        if start_time is None:
            start_time = time_type(9, 0)  # Different from template default
        if end_time is None:
            end_time = time_type(17, 0)
    else:
        # Day off - times should be null
        start_time = None
        end_time = None

    data = {
        "employee_id": employee_id,
        "date": override_date,
        "start_time": start_time,
        "end_time": end_time,
        "is_day_off": is_day_off,
    }
    data.update(overrides)

    override = ShiftScheduleOverride(**data)
    db.add(override)
    db.flush()
    return override
