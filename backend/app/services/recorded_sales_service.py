"""
Recorded Sales Service

Handles operations for manually recorded sales during daily operations:
- Recording individual sales
- Voiding sales (soft delete with reason)
- Querying day sales and totals
- Automatic shift attribution

Business Rules:
- Sales can only be recorded when day is open
- Prices are taken from product variant (never from client)
- Voided sales are soft-deleted for audit trail
- Error messages in Polish
"""

import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional
from datetime import datetime
from decimal import Decimal

from app.models.daily_record import DailyRecord, DayStatus
from app.models.product import ProductVariant
from app.models.shift_assignment import ShiftAssignment
from app.models.recorded_sale import RecordedSale, VoidReason
from app.core.i18n import t

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def _get_active_shift(
    db: Session,
    daily_record_id: int
) -> Optional[ShiftAssignment]:
    """
    Find shift assignment that covers the current time.

    Used for automatic shift attribution when recording sales.

    Args:
        db: Database session
        daily_record_id: ID of the daily record

    Returns:
        ShiftAssignment if a matching shift is found, None otherwise
    """
    current_time = datetime.now().time()

    # Find shift where current time is between start and end
    shift = db.query(ShiftAssignment).filter(
        ShiftAssignment.daily_record_id == daily_record_id,
        ShiftAssignment.start_time <= current_time,
        ShiftAssignment.end_time > current_time
    ).first()

    return shift


# -----------------------------------------------------------------------------
# Record Sale
# -----------------------------------------------------------------------------

def record_sale(
    db: Session,
    daily_record_id: int,
    variant_id: int,
    quantity: int = 1
) -> tuple[Optional[RecordedSale], Optional[str]]:
    """
    Record a sale for a product variant.

    Business Rules:
    - Day must be open (status == DayStatus.OPEN)
    - Product variant must exist and be active
    - Price is taken from variant.price_pln (never from client!)
    - Automatically finds and assigns current shift for attribution

    Args:
        db: Database session
        daily_record_id: ID of the open daily record
        variant_id: ID of the product variant being sold
        quantity: Number of items sold (default: 1)

    Returns:
        Tuple of (RecordedSale, None) on success, or (None, error_message) on failure
    """
    # Validate day exists and is open
    daily_record = db.query(DailyRecord).filter(
        DailyRecord.id == daily_record_id
    ).first()

    if not daily_record:
        return None, t("errors.daily_record_not_found")

    if daily_record.status != DayStatus.OPEN:
        return None, t("errors.day_not_open")

    # Validate product variant exists and is active
    variant = db.query(ProductVariant).filter(
        ProductVariant.id == variant_id
    ).first()

    if not variant:
        return None, t("errors.product_not_found_or_inactive")

    if not variant.is_active:
        return None, t("errors.product_not_found_or_inactive")

    # Get current price from variant (NEVER from client input!)
    unit_price = Decimal(str(variant.price_pln))

    # Find active shift for attribution (optional)
    shift_assignment = _get_active_shift(db, daily_record_id)
    shift_assignment_id = shift_assignment.id if shift_assignment else None

    # Create the recorded sale
    recorded_sale = RecordedSale(
        daily_record_id=daily_record_id,
        product_variant_id=variant_id,
        shift_assignment_id=shift_assignment_id,
        quantity=quantity,
        unit_price_pln=unit_price,
        recorded_at=datetime.now(),
    )

    db.add(recorded_sale)
    db.commit()
    db.refresh(recorded_sale)

    logger.info(
        f"Zarejestrowano sprzedaz: wariant {variant_id}, "
        f"ilosc {quantity}, cena {unit_price} PLN"
    )

    return recorded_sale, None


# -----------------------------------------------------------------------------
# Void Sale
# -----------------------------------------------------------------------------

def void_sale(
    db: Session,
    sale_id: int,
    reason: VoidReason,
    notes: Optional[str] = None
) -> tuple[Optional[RecordedSale], Optional[str]]:
    """
    Void (soft-delete) a recorded sale.

    Business Rules:
    - Sale must exist and not already be voided
    - Day must still be open (cannot void sales from closed days)
    - Sets voided_at timestamp, void_reason, and optional notes
    - Preserves record for audit trail

    Args:
        db: Database session
        sale_id: ID of the sale to void
        reason: Reason for voiding (from VoidReason enum)
        notes: Optional additional notes about the void

    Returns:
        Tuple of (RecordedSale, None) on success, or (None, error_message) on failure
    """
    # Get the sale
    sale = db.query(RecordedSale).filter(
        RecordedSale.id == sale_id
    ).first()

    if not sale:
        return None, t("errors.sale_not_found_or_voided")

    if sale.is_voided:
        return None, t("errors.sale_not_found_or_voided")

    # Validate day is still open
    daily_record = db.query(DailyRecord).filter(
        DailyRecord.id == sale.daily_record_id
    ).first()

    if not daily_record:
        return None, t("errors.daily_record_not_found")

    if daily_record.status != DayStatus.OPEN:
        return None, t("errors.cannot_void_sale_closed_day")

    # Void the sale (soft delete)
    sale.voided_at = datetime.now()
    sale.void_reason = reason
    sale.void_notes = notes

    db.commit()
    db.refresh(sale)

    logger.info(
        f"Anulowano sprzedaz ID {sale_id}: "
        f"powod={reason.value}, notatki={notes}"
    )

    return sale, None


# -----------------------------------------------------------------------------
# Get Day Sales
# -----------------------------------------------------------------------------

def get_day_sales(
    db: Session,
    daily_record_id: int,
    include_voided: bool = False
) -> list[RecordedSale]:
    """
    Get all recorded sales for a day.

    Args:
        db: Database session
        daily_record_id: ID of the daily record
        include_voided: If True, includes voided sales in results

    Returns:
        List of RecordedSale records, ordered by recorded_at DESC
    """
    query = db.query(RecordedSale).filter(
        RecordedSale.daily_record_id == daily_record_id
    )

    if not include_voided:
        query = query.filter(RecordedSale.voided_at.is_(None))

    return query.order_by(desc(RecordedSale.recorded_at)).all()


# -----------------------------------------------------------------------------
# Get Day Total
# -----------------------------------------------------------------------------

def get_day_total(
    db: Session,
    daily_record_id: int
) -> dict:
    """
    Calculate total revenue from recorded sales for a day.

    Excludes voided sales from calculations.

    Args:
        db: Database session
        daily_record_id: ID of the daily record

    Returns:
        Dictionary with:
        - total_pln: Total revenue (Decimal)
        - sales_count: Number of sale records (int)
        - items_count: Total quantity of items sold (int)
    """
    # Query non-voided sales
    sales = db.query(RecordedSale).filter(
        RecordedSale.daily_record_id == daily_record_id,
        RecordedSale.voided_at.is_(None)
    ).all()

    total_pln = Decimal("0")
    sales_count = len(sales)
    items_count = 0

    for sale in sales:
        total_pln += sale.total_pln
        items_count += sale.quantity

    return {
        "total_pln": total_pln,
        "sales_count": sales_count,
        "items_count": items_count,
    }


# -----------------------------------------------------------------------------
# Get Day Total (Aggregated Query - Alternative)
# -----------------------------------------------------------------------------

def get_day_total_aggregated(
    db: Session,
    daily_record_id: int
) -> dict:
    """
    Calculate total revenue using SQL aggregation.

    More efficient for large datasets than get_day_total().
    Excludes voided sales from calculations.

    Args:
        db: Database session
        daily_record_id: ID of the daily record

    Returns:
        Dictionary with:
        - total_pln: Total revenue (Decimal)
        - sales_count: Number of sale records (int)
        - items_count: Total quantity of items sold (int)
    """
    result = db.query(
        func.count(RecordedSale.id).label("sales_count"),
        func.coalesce(func.sum(RecordedSale.quantity), 0).label("items_count"),
        func.coalesce(
            func.sum(RecordedSale.quantity * RecordedSale.unit_price_pln),
            Decimal("0")
        ).label("total_pln")
    ).filter(
        RecordedSale.daily_record_id == daily_record_id,
        RecordedSale.voided_at.is_(None)
    ).first()

    return {
        "total_pln": Decimal(str(result.total_pln)) if result.total_pln else Decimal("0"),
        "sales_count": result.sales_count or 0,
        "items_count": result.items_count or 0,
    }
