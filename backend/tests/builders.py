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
    **overrides
) -> Delivery:
    """Create a delivery record with sensible defaults."""
    data = {
        "daily_record_id": daily_record_id,
        "ingredient_id": ingredient_id,
        "quantity": quantity,
        "price_pln": price_pln,
    }
    data.update(overrides)

    delivery = Delivery(**data)
    db.add(delivery)
    db.flush()
    return delivery
