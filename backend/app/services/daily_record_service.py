from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from app.models.daily_record import DailyRecord, DayStatus
from app.models.inventory_snapshot import InventorySnapshot, SnapshotType
from app.models.sales_item import SalesItem
from app.models.transaction import Transaction, TransactionType
from app.schemas.daily_record import DailyRecordCreate, DailyRecordClose, DailyRecordSummary
from app.services import inventory_service


def get_daily_records(db: Session, skip: int = 0, limit: int = 30) -> tuple[list[DailyRecord], int]:
    total = db.query(func.count(DailyRecord.id)).scalar()
    items = db.query(DailyRecord).order_by(DailyRecord.date.desc()).offset(skip).limit(limit).all()
    return items, total


def get_daily_record(db: Session, record_id: int) -> Optional[DailyRecord]:
    return db.query(DailyRecord).filter(DailyRecord.id == record_id).first()


def get_today_record(db: Session) -> Optional[DailyRecord]:
    today = date.today()
    return db.query(DailyRecord).filter(DailyRecord.date == today).first()


def get_record_by_date(db: Session, record_date: date) -> Optional[DailyRecord]:
    return db.query(DailyRecord).filter(DailyRecord.date == record_date).first()


def open_day(db: Session, data: DailyRecordCreate) -> Optional[DailyRecord]:
    # Check if already exists
    existing = get_record_by_date(db, data.date)
    if existing:
        return None

    # Create daily record
    db_record = DailyRecord(
        date=data.date,
        status=DayStatus.OPEN,
        notes=data.notes,
    )
    db.add(db_record)
    db.flush()

    # Create opening inventory snapshots
    for snap in data.opening_inventory:
        db_snap = InventorySnapshot(
            daily_record_id=db_record.id,
            ingredient_id=snap.ingredient_id,
            snapshot_type=SnapshotType.OPEN,
            quantity_grams=snap.quantity_grams,
            quantity_count=snap.quantity_count,
        )
        db.add(db_snap)

    db.commit()
    db.refresh(db_record)
    return db_record


def close_day(db: Session, record_id: int, data: DailyRecordClose) -> Optional[DailyRecord]:
    db_record = get_daily_record(db, record_id)
    if not db_record or db_record.status == DayStatus.CLOSED:
        return None

    # Create closing inventory snapshots
    for snap in data.closing_inventory:
        db_snap = InventorySnapshot(
            daily_record_id=db_record.id,
            ingredient_id=snap.ingredient_id,
            snapshot_type=SnapshotType.CLOSE,
            quantity_grams=snap.quantity_grams,
            quantity_count=snap.quantity_count,
        )
        db.add(db_snap)

    # Update record
    db_record.status = DayStatus.CLOSED
    db_record.closed_at = datetime.now()
    if data.notes:
        db_record.notes = data.notes

    db.commit()
    db.refresh(db_record)
    return db_record


def get_daily_summary(db: Session, record_id: int) -> Optional[DailyRecordSummary]:
    db_record = get_daily_record(db, record_id)
    if not db_record:
        return None

    # Calculate sales totals
    sales_result = db.query(
        func.count(SalesItem.id),
        func.sum(SalesItem.quantity_sold),
        func.sum(SalesItem.total_price)
    ).filter(SalesItem.daily_record_id == record_id).first()

    items_sold = sales_result[1] or 0
    total_sales = Decimal(str(sales_result[2] or 0))

    # Calculate revenue (sales + revenue transactions)
    revenue_result = db.query(func.sum(Transaction.amount)).filter(
        Transaction.daily_record_id == record_id,
        Transaction.type == TransactionType.REVENUE
    ).scalar() or Decimal("0")
    total_revenue = total_sales + Decimal(str(revenue_result))

    # Calculate expenses
    expenses_result = db.query(func.sum(Transaction.amount)).filter(
        Transaction.daily_record_id == record_id,
        Transaction.type == TransactionType.EXPENSE
    ).scalar() or Decimal("0")

    # Get discrepancies if day is closed
    discrepancies = []
    if db_record.status == DayStatus.CLOSED:
        discrepancies = inventory_service.calculate_discrepancies(db, record_id)

    return DailyRecordSummary(
        id=db_record.id,
        date=db_record.date,
        status=db_record.status,
        opened_at=db_record.opened_at,
        closed_at=db_record.closed_at,
        notes=db_record.notes,
        created_at=db_record.created_at,
        total_sales=total_sales,
        total_revenue=total_revenue,
        total_expenses=Decimal(str(expenses_result)),
        items_sold=items_sold,
        discrepancies=discrepancies,
    )
