"""
Batch Service

Handles batch/expiry tracking operations:
- Auto-generating batch numbers (B-YYYYMMDD-NNN)
- Creating batches from deliveries
- FIFO tracking (informational)
- Expiry alerts (7 days before expiration)
- Batch deductions with audit trail

Business Rules:
- Batch numbers are unique and auto-generated
- Batches are created automatically when deliveries arrive
- Expiry alerts triggered at 7 days (warning) and 2 days (critical)
- FIFO is informational only (shows ages, doesn't enforce)
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from typing import Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

from app.models.ingredient_batch import IngredientBatch, BatchDeduction
from app.models.ingredient import Ingredient
from app.models.delivery import DeliveryItem
from app.core.i18n import t

from app.schemas.batch import (
    BatchCreate,
    BatchResponse,
    BatchListResponse,
    BatchDeductionCreate,
    BatchDeductionResponse,
    ExpiryAlertResponse,
    ExpiryAlertsListResponse,
    AlertLevel,
    BatchInventoryItem,
    IngredientBatchSummary,
    EXPIRY_ALERT_DAYS,
    EXPIRY_CRITICAL_DAYS,
)


# -----------------------------------------------------------------------------
# Batch Number Generation
# -----------------------------------------------------------------------------

def generate_batch_number(db: Session) -> str:
    """
    Generate unique batch number in format: B-YYYYMMDD-NNN

    Example: B-20260105-001, B-20260105-002, etc.

    The NNN part increments based on existing batches created today.
    """
    today = date.today()
    date_str = today.strftime("%Y%m%d")
    prefix = f"B-{date_str}-"

    # Find highest batch number for today
    existing = db.query(IngredientBatch.batch_number).filter(
        IngredientBatch.batch_number.like(f"{prefix}%")
    ).all()

    if not existing:
        return f"{prefix}001"

    # Extract sequence numbers and find max
    max_seq = 0
    for (batch_number,) in existing:
        try:
            seq_str = batch_number.replace(prefix, "")
            seq = int(seq_str)
            max_seq = max(max_seq, seq)
        except (ValueError, AttributeError):
            continue

    next_seq = max_seq + 1
    return f"{prefix}{next_seq:03d}"


# -----------------------------------------------------------------------------
# Batch Creation
# -----------------------------------------------------------------------------

def create_batch_from_delivery_item(
    db: Session,
    delivery_item: DeliveryItem,
    location: str = "storage"
) -> IngredientBatch:
    """
    Auto-create a batch when a delivery item arrives.

    Args:
        db: Database session
        delivery_item: The delivery item to create batch from
        location: Initial location ('storage' or 'shop')

    Returns:
        Created IngredientBatch instance
    """
    batch_number = generate_batch_number(db)

    db_batch = IngredientBatch(
        batch_number=batch_number,
        ingredient_id=delivery_item.ingredient_id,
        delivery_item_id=delivery_item.id,
        expiry_date=delivery_item.expiry_date,
        initial_quantity=delivery_item.quantity,
        remaining_quantity=delivery_item.quantity,
        location=location,
        is_active=True,
    )
    db.add(db_batch)
    db.flush()  # Get ID without committing

    logger.info(
        f"Created batch {batch_number} for ingredient_id={delivery_item.ingredient_id}, "
        f"quantity={delivery_item.quantity}, expiry={delivery_item.expiry_date}"
    )

    return db_batch


def create_batch_manual(
    db: Session,
    data: BatchCreate
) -> tuple[Optional[BatchResponse], Optional[str]]:
    """
    Manually create a batch (rare case, usually auto-created from deliveries).

    Returns:
        Tuple of (response, error_message).
    """
    # Validate ingredient exists
    ingredient = db.query(Ingredient).filter(Ingredient.id == data.ingredient_id).first()
    if not ingredient:
        return None, t("errors.ingredient_id_not_found", id=data.ingredient_id)

    if not ingredient.is_active:
        return None, t("errors.ingredient_inactive", name=ingredient.name)

    batch_number = generate_batch_number(db)

    db_batch = IngredientBatch(
        batch_number=batch_number,
        ingredient_id=data.ingredient_id,
        delivery_item_id=None,
        expiry_date=data.expiry_date,
        initial_quantity=data.initial_quantity,
        remaining_quantity=data.initial_quantity,
        location=data.location.value,
        is_active=True,
        notes=data.notes,
    )
    db.add(db_batch)
    db.commit()
    db.refresh(db_batch)

    return _build_batch_response(db_batch, ingredient), None


# -----------------------------------------------------------------------------
# Batch Queries
# -----------------------------------------------------------------------------

def get_batch_by_id(
    db: Session,
    batch_id: int
) -> tuple[Optional[BatchResponse], Optional[str]]:
    """Get a single batch by ID."""
    batch = db.query(IngredientBatch).options(
        joinedload(IngredientBatch.ingredient)
    ).filter(IngredientBatch.id == batch_id).first()

    if not batch:
        return None, t("errors.batch_not_found")

    return _build_batch_response(batch, batch.ingredient), None


def get_batches_for_ingredient(
    db: Session,
    ingredient_id: int,
    location: Optional[str] = None,
    active_only: bool = True
) -> BatchListResponse:
    """
    Get all batches for an ingredient, ordered by FIFO (created_at asc).

    Args:
        db: Database session
        ingredient_id: ID of the ingredient
        location: Optional filter by location ('storage' or 'shop')
        active_only: If True, only return batches with remaining quantity > 0

    Returns:
        BatchListResponse with batches in FIFO order
    """
    query = db.query(IngredientBatch).options(
        joinedload(IngredientBatch.ingredient)
    ).filter(IngredientBatch.ingredient_id == ingredient_id)

    if location:
        query = query.filter(IngredientBatch.location == location)

    if active_only:
        query = query.filter(
            IngredientBatch.is_active == True,
            IngredientBatch.remaining_quantity > 0
        )

    # FIFO: Order by creation date (oldest first)
    batches = query.order_by(IngredientBatch.created_at.asc()).all()

    items = []
    expiring_soon_count = 0

    for batch in batches:
        response = _build_batch_response(batch, batch.ingredient)
        items.append(response)
        if response.is_expiring_soon:
            expiring_soon_count += 1

    return BatchListResponse(
        items=items,
        total=len(items),
        expiring_soon_count=expiring_soon_count
    )


# -----------------------------------------------------------------------------
# Expiry Alerts
# -----------------------------------------------------------------------------

def get_expiry_alerts(
    db: Session,
    days_ahead: int = EXPIRY_ALERT_DAYS
) -> ExpiryAlertsListResponse:
    """
    Get all batches expiring within the specified days.

    Classifies alerts as:
    - 'expired': Already past expiry date
    - 'critical': 0-2 days until expiry
    - 'warning': 3-7 days until expiry

    Args:
        db: Database session
        days_ahead: Number of days to look ahead (default: 7)

    Returns:
        ExpiryAlertsListResponse with categorized alerts
    """
    today = date.today()
    alert_cutoff = today + timedelta(days=days_ahead)

    # Get active batches with expiry dates within range
    batches = db.query(IngredientBatch).options(
        joinedload(IngredientBatch.ingredient)
    ).filter(
        IngredientBatch.is_active == True,
        IngredientBatch.remaining_quantity > 0,
        IngredientBatch.expiry_date.isnot(None),
        IngredientBatch.expiry_date <= alert_cutoff
    ).order_by(IngredientBatch.expiry_date.asc()).all()

    alerts = []
    expired_count = 0
    critical_count = 0
    warning_count = 0

    for batch in batches:
        days_until = (batch.expiry_date - today).days

        # Determine alert level
        if days_until < 0:
            alert_level = AlertLevel.EXPIRED
            expired_count += 1
        elif days_until <= EXPIRY_CRITICAL_DAYS:
            alert_level = AlertLevel.CRITICAL
            critical_count += 1
        else:
            alert_level = AlertLevel.WARNING
            warning_count += 1

        alert = ExpiryAlertResponse(
            batch_id=batch.id,
            batch_number=batch.batch_number,
            ingredient_id=batch.ingredient_id,
            ingredient_name=batch.ingredient.name,
            unit_label=batch.ingredient.unit_label or "szt",
            expiry_date=batch.expiry_date,
            remaining_quantity=Decimal(str(batch.remaining_quantity)),
            location=batch.location,
            days_until_expiry=days_until,
            alert_level=alert_level,
        )
        alerts.append(alert)

    return ExpiryAlertsListResponse(
        alerts=alerts,
        total=len(alerts),
        expired_count=expired_count,
        critical_count=critical_count,
        warning_count=warning_count,
    )


# -----------------------------------------------------------------------------
# Batch Deductions
# -----------------------------------------------------------------------------

def deduct_from_batch(
    db: Session,
    batch_id: int,
    quantity: Decimal,
    reason: str,
    daily_record_id: Optional[int] = None,
    reference_type: Optional[str] = None,
    reference_id: Optional[int] = None,
    notes: Optional[str] = None
) -> tuple[Optional[BatchDeductionResponse], Optional[str]]:
    """
    Deduct quantity from a batch and create audit record.

    Marks batch as inactive if fully depleted.

    Args:
        db: Database session
        batch_id: ID of the batch to deduct from
        quantity: Amount to deduct
        reason: Reason for deduction (sales, spoilage, transfer, adjustment)
        daily_record_id: Optional associated daily record
        reference_type: Type of related record (e.g., 'spoilage')
        reference_id: ID of related record
        notes: Optional notes

    Returns:
        Tuple of (deduction_response, error_message)
    """
    batch = db.query(IngredientBatch).filter(IngredientBatch.id == batch_id).first()
    if not batch:
        return None, t("errors.batch_not_found")

    if not batch.is_active:
        return None, t("errors.batch_inactive")

    remaining = Decimal(str(batch.remaining_quantity))
    quantity = Decimal(str(quantity))

    if quantity > remaining:
        return None, t("errors.batch_insufficient_quantity", available=remaining)

    # Update batch
    batch.remaining_quantity = remaining - quantity

    # Mark as inactive if depleted
    if batch.remaining_quantity <= 0:
        batch.is_active = False

    # Create audit record
    db_deduction = BatchDeduction(
        batch_id=batch_id,
        daily_record_id=daily_record_id,
        quantity=quantity,
        reason=reason,
        reference_type=reference_type,
        reference_id=reference_id,
        notes=notes,
    )
    db.add(db_deduction)
    db.commit()
    db.refresh(db_deduction)

    response = BatchDeductionResponse(
        id=db_deduction.id,
        batch_id=db_deduction.batch_id,
        batch_number=batch.batch_number,
        daily_record_id=db_deduction.daily_record_id,
        quantity=Decimal(str(db_deduction.quantity)),
        reason=db_deduction.reason,
        reference_type=db_deduction.reference_type,
        reference_id=db_deduction.reference_id,
        notes=db_deduction.notes,
        created_at=db_deduction.created_at,
    )

    logger.info(
        f"Deducted {quantity} from batch {batch.batch_number}, "
        f"reason={reason}, remaining={batch.remaining_quantity}"
    )

    return response, None


# -----------------------------------------------------------------------------
# Ingredient Batch Summary (FIFO Display)
# -----------------------------------------------------------------------------

def get_ingredient_batch_summary(
    db: Session,
    ingredient_id: int,
    location: Optional[str] = None
) -> tuple[Optional[IngredientBatchSummary], Optional[str]]:
    """
    Get summary of all batches for an ingredient with FIFO ordering.

    Args:
        db: Database session
        ingredient_id: ID of the ingredient
        location: Optional filter by location

    Returns:
        Tuple of (summary, error_message)
    """
    ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not ingredient:
        return None, t("errors.ingredient_id_not_found", id=ingredient_id)

    query = db.query(IngredientBatch).filter(
        IngredientBatch.ingredient_id == ingredient_id,
        IngredientBatch.is_active == True,
        IngredientBatch.remaining_quantity > 0
    )

    if location:
        query = query.filter(IngredientBatch.location == location)

    # FIFO ordering: oldest first
    batches = query.order_by(IngredientBatch.created_at.asc()).all()

    today = date.today()
    total_quantity = Decimal("0")
    expiring_soon_count = 0
    batch_items = []

    for idx, batch in enumerate(batches, start=1):
        remaining = Decimal(str(batch.remaining_quantity))
        total_quantity += remaining

        # Calculate expiry info
        days_until = None
        is_expiring = False
        if batch.expiry_date:
            days_until = (batch.expiry_date - today).days
            is_expiring = days_until <= EXPIRY_ALERT_DAYS
            if is_expiring:
                expiring_soon_count += 1

        batch_item = BatchInventoryItem(
            id=batch.id,
            batch_number=batch.batch_number,
            expiry_date=batch.expiry_date,
            remaining_quantity=remaining,
            location=batch.location,
            is_active=batch.is_active,
            created_at=batch.created_at,
            fifo_order=idx,
            days_until_expiry=days_until,
            is_expiring_soon=is_expiring,
        )
        batch_items.append(batch_item)

    summary = IngredientBatchSummary(
        ingredient_id=ingredient_id,
        ingredient_name=ingredient.name,
        unit_label=ingredient.unit_label or "szt",
        total_quantity=total_quantity,
        active_batch_count=len(batch_items),
        expiring_soon_count=expiring_soon_count,
        batches=batch_items,
    )

    return summary, None


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def _build_batch_response(batch: IngredientBatch, ingredient: Ingredient) -> BatchResponse:
    """Build BatchResponse from model with calculated fields."""
    today = date.today()

    # Calculate days until expiry
    days_until = None
    is_expiring = False
    if batch.expiry_date:
        days_until = (batch.expiry_date - today).days
        is_expiring = days_until <= EXPIRY_ALERT_DAYS

    # Calculate age in days
    age_days = 0
    if batch.created_at:
        created_date = batch.created_at.date() if hasattr(batch.created_at, 'date') else batch.created_at
        age_days = (today - created_date).days

    return BatchResponse(
        id=batch.id,
        batch_number=batch.batch_number,
        ingredient_id=batch.ingredient_id,
        ingredient_name=ingredient.name,
        unit_label=ingredient.unit_label or "szt",
        delivery_item_id=batch.delivery_item_id,
        expiry_date=batch.expiry_date,
        initial_quantity=Decimal(str(batch.initial_quantity)),
        remaining_quantity=Decimal(str(batch.remaining_quantity)),
        location=batch.location,
        is_active=batch.is_active,
        notes=batch.notes,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
        days_until_expiry=days_until,
        is_expiring_soon=is_expiring,
        age_days=age_days,
    )
