"""
Mid-Day Operations Service

Handles CRUD operations for mid-day events during an open day:
- Deliveries: Ingredient deliveries with cost tracking
- Storage Transfers: Moving ingredients from storage to shop
- Spoilage: Recording wasted/damaged ingredients

Business Rules:
- Can only add/modify events for an OPEN day
- All quantities use decimal format
- Error messages in Polish
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import Optional
from datetime import datetime
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

from app.models.daily_record import DailyRecord, DayStatus
from app.models.ingredient import Ingredient
from app.models.delivery import Delivery
from app.models.storage_transfer import StorageTransfer
from app.models.spoilage import Spoilage, SpoilageReason
from app.models.storage_inventory import StorageInventory

from app.schemas.mid_day_operations import (
    DeliveryCreate,
    DeliveryResponse,
    DeliveryListResponse,
    StorageTransferCreate,
    StorageTransferResponse,
    StorageTransferListResponse,
    SpoilageCreate,
    SpoilageResponse,
    SpoilageListResponse,
    SPOILAGE_REASON_LABELS,
    SpoilageReasonEnum,
)
from app.core.i18n import t


# -----------------------------------------------------------------------------
# Validation Helpers
# -----------------------------------------------------------------------------

def _validate_daily_record_open(db: Session, daily_record_id: int) -> tuple[Optional[DailyRecord], Optional[str]]:
    """
    Validate that daily_record_id exists and the day is open.
    Returns (record, error_message).
    """
    record = db.query(DailyRecord).filter(DailyRecord.id == daily_record_id).first()
    if not record:
        return None, t("errors.daily_record_id_not_found", id=daily_record_id)

    if record.status != DayStatus.OPEN:
        return None, t("errors.cannot_add_to_closed_day")

    return record, None


def _validate_ingredient_active(db: Session, ingredient_id: int) -> tuple[Optional[Ingredient], Optional[str]]:
    """
    Validate that ingredient exists and is active.
    Returns (ingredient, error_message).
    """
    ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not ingredient:
        return None, t("errors.ingredient_id_not_found", id=ingredient_id)

    if not ingredient.is_active:
        return None, t("errors.ingredient_inactive", name=ingredient.name)

    return ingredient, None


def _validate_storage_inventory_sufficient(
    db: Session,
    ingredient_id: int,
    requested_quantity: Decimal
) -> tuple[Optional[Decimal], Optional[str]]:
    """
    Validate that storage inventory has sufficient quantity for transfer.
    VR-10: Storage transfer <= storage inventory (BLOCK)

    Returns (available_quantity, error_message).
    """
    storage = db.query(StorageInventory).filter(
        StorageInventory.ingredient_id == ingredient_id
    ).first()

    available = Decimal("0")
    if storage:
        available = Decimal(str(storage.quantity))

    if requested_quantity > available:
        return None, t("errors.insufficient_storage", available=available)

    return available, None


# -----------------------------------------------------------------------------
# Delivery CRUD
# -----------------------------------------------------------------------------

def create_delivery(
    db: Session,
    data: DeliveryCreate
) -> tuple[Optional[DeliveryResponse], Optional[str]]:
    """
    Create a new delivery record.

    Returns:
        Tuple of (response, error_message). If error_message is not None, operation failed.
    """
    # Validate daily record
    daily_record, error = _validate_daily_record_open(db, data.daily_record_id)
    if error:
        return None, error

    # Validate ingredient
    ingredient, error = _validate_ingredient_active(db, data.ingredient_id)
    if error:
        return None, error

    try:
        # Create delivery
        db_delivery = Delivery(
            daily_record_id=data.daily_record_id,
            ingredient_id=data.ingredient_id,
            quantity=data.quantity,
            price_pln=data.price_pln,
            delivered_at=data.delivered_at or datetime.now(),
        )
        db.add(db_delivery)
        db.commit()
        db.refresh(db_delivery)

        return _build_delivery_response(db_delivery, ingredient), None
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Blad integralnosci bazy danych przy tworzeniu dostawy: {e}")
        return None, t("errors.database_integrity_error")


def get_deliveries(
    db: Session,
    daily_record_id: Optional[int] = None
) -> DeliveryListResponse:
    """
    Get list of deliveries, optionally filtered by daily_record_id.
    Uses eager loading to avoid N+1 queries.
    """
    query = db.query(Delivery).options(joinedload(Delivery.ingredient))

    if daily_record_id is not None:
        query = query.filter(Delivery.daily_record_id == daily_record_id)

    deliveries = query.order_by(Delivery.delivered_at.desc()).all()

    items = [
        _build_delivery_response(delivery, delivery.ingredient)
        for delivery in deliveries
        if delivery.ingredient
    ]

    return DeliveryListResponse(items=items, total=len(items))


def get_delivery_by_id(
    db: Session,
    delivery_id: int
) -> tuple[Optional[DeliveryResponse], Optional[str]]:
    """
    Get a single delivery by ID.
    """
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        return None, t("errors.delivery_not_found")

    ingredient = db.query(Ingredient).filter(Ingredient.id == delivery.ingredient_id).first()
    if not ingredient:
        return None, t("errors.ingredient_not_found")

    return _build_delivery_response(delivery, ingredient), None


def delete_delivery(
    db: Session,
    delivery_id: int
) -> tuple[bool, Optional[str]]:
    """
    Delete a delivery record.
    Can only delete from an open day.

    Returns:
        Tuple of (success, error_message).
    """
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        return False, t("errors.delivery_not_found")

    # Validate daily record is still open
    daily_record = db.query(DailyRecord).filter(DailyRecord.id == delivery.daily_record_id).first()
    if daily_record and daily_record.status != DayStatus.OPEN:
        return False, t("errors.cannot_delete_delivery_closed")

    db.delete(delivery)
    db.commit()

    return True, None


def _build_delivery_response(delivery: Delivery, ingredient: Ingredient) -> DeliveryResponse:
    """Build response schema from delivery model."""
    return DeliveryResponse(
        id=delivery.id,
        daily_record_id=delivery.daily_record_id,
        ingredient_id=delivery.ingredient_id,
        ingredient_name=ingredient.name,
        unit_label=ingredient.unit_label or "szt",
        quantity=Decimal(str(delivery.quantity)),
        price_pln=Decimal(str(delivery.price_pln)),
        delivered_at=delivery.delivered_at,
        created_at=delivery.created_at,
    )


# -----------------------------------------------------------------------------
# Storage Transfer CRUD
# -----------------------------------------------------------------------------

def create_storage_transfer(
    db: Session,
    data: StorageTransferCreate
) -> tuple[Optional[StorageTransferResponse], Optional[str]]:
    """
    Create a new storage transfer record.

    VR-10: Validates that transfer quantity does not exceed storage inventory.

    Returns:
        Tuple of (response, error_message). If error_message is not None, operation failed.
    """
    # Validate daily record
    daily_record, error = _validate_daily_record_open(db, data.daily_record_id)
    if error:
        return None, error

    # Validate ingredient
    ingredient, error = _validate_ingredient_active(db, data.ingredient_id)
    if error:
        return None, error

    # VR-10: Validate storage inventory has sufficient quantity
    _, error = _validate_storage_inventory_sufficient(
        db, data.ingredient_id, Decimal(str(data.quantity))
    )
    if error:
        return None, error

    try:
        # Create transfer
        db_transfer = StorageTransfer(
            daily_record_id=data.daily_record_id,
            ingredient_id=data.ingredient_id,
            quantity=data.quantity,
            transferred_at=data.transferred_at or datetime.now(),
        )
        db.add(db_transfer)

        # Update storage inventory (deduct transferred quantity)
        storage = db.query(StorageInventory).filter(
            StorageInventory.ingredient_id == data.ingredient_id
        ).first()
        if storage:
            storage.quantity = Decimal(str(storage.quantity)) - Decimal(str(data.quantity))

        db.commit()
        db.refresh(db_transfer)

        return _build_transfer_response(db_transfer, ingredient), None
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Blad integralnosci bazy danych przy tworzeniu transferu: {e}")
        return None, t("errors.database_integrity_error")


def get_storage_transfers(
    db: Session,
    daily_record_id: Optional[int] = None
) -> StorageTransferListResponse:
    """
    Get list of storage transfers, optionally filtered by daily_record_id.
    Uses eager loading to avoid N+1 queries.
    """
    query = db.query(StorageTransfer).options(joinedload(StorageTransfer.ingredient))

    if daily_record_id is not None:
        query = query.filter(StorageTransfer.daily_record_id == daily_record_id)

    transfers = query.order_by(StorageTransfer.transferred_at.desc()).all()

    items = [
        _build_transfer_response(transfer, transfer.ingredient)
        for transfer in transfers
        if transfer.ingredient
    ]

    return StorageTransferListResponse(items=items, total=len(items))


def get_storage_transfer_by_id(
    db: Session,
    transfer_id: int
) -> tuple[Optional[StorageTransferResponse], Optional[str]]:
    """
    Get a single storage transfer by ID.
    """
    transfer = db.query(StorageTransfer).filter(StorageTransfer.id == transfer_id).first()
    if not transfer:
        return None, t("errors.transfer_not_found")

    ingredient = db.query(Ingredient).filter(Ingredient.id == transfer.ingredient_id).first()
    if not ingredient:
        return None, t("errors.ingredient_not_found")

    return _build_transfer_response(transfer, ingredient), None


def delete_storage_transfer(
    db: Session,
    transfer_id: int
) -> tuple[bool, Optional[str]]:
    """
    Delete a storage transfer record.
    Can only delete from an open day.
    Restores the quantity back to storage inventory.

    Returns:
        Tuple of (success, error_message).
    """
    transfer = db.query(StorageTransfer).filter(StorageTransfer.id == transfer_id).first()
    if not transfer:
        return False, t("errors.transfer_not_found")

    # Validate daily record is still open
    daily_record = db.query(DailyRecord).filter(DailyRecord.id == transfer.daily_record_id).first()
    if daily_record and daily_record.status != DayStatus.OPEN:
        return False, t("errors.cannot_delete_transfer_closed")

    # Restore quantity to storage inventory
    storage = db.query(StorageInventory).filter(
        StorageInventory.ingredient_id == transfer.ingredient_id
    ).first()
    if storage:
        storage.quantity = Decimal(str(storage.quantity)) + Decimal(str(transfer.quantity))

    db.delete(transfer)
    db.commit()

    return True, None


def _build_transfer_response(transfer: StorageTransfer, ingredient: Ingredient) -> StorageTransferResponse:
    """Build response schema from transfer model."""
    return StorageTransferResponse(
        id=transfer.id,
        daily_record_id=transfer.daily_record_id,
        ingredient_id=transfer.ingredient_id,
        ingredient_name=ingredient.name,
        unit_label=ingredient.unit_label or "szt",
        quantity=Decimal(str(transfer.quantity)),
        transferred_at=transfer.transferred_at,
        created_at=transfer.created_at,
    )


# -----------------------------------------------------------------------------
# Spoilage CRUD
# -----------------------------------------------------------------------------

def create_spoilage(
    db: Session,
    data: SpoilageCreate
) -> tuple[Optional[SpoilageResponse], Optional[str]]:
    """
    Create a new spoilage record.

    Returns:
        Tuple of (response, error_message). If error_message is not None, operation failed.
    """
    # Validate daily record
    daily_record, error = _validate_daily_record_open(db, data.daily_record_id)
    if error:
        return None, error

    # Validate ingredient
    ingredient, error = _validate_ingredient_active(db, data.ingredient_id)
    if error:
        return None, error

    # Convert schema enum to model enum
    reason_value = SpoilageReason(data.reason.value)

    try:
        # Create spoilage
        db_spoilage = Spoilage(
            daily_record_id=data.daily_record_id,
            ingredient_id=data.ingredient_id,
            quantity=data.quantity,
            reason=reason_value,
            notes=data.notes,
            recorded_at=data.recorded_at or datetime.now(),
        )
        db.add(db_spoilage)
        db.commit()
        db.refresh(db_spoilage)

        return _build_spoilage_response(db_spoilage, ingredient), None
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Blad integralnosci bazy danych przy tworzeniu straty: {e}")
        return None, t("errors.database_integrity_error")


def get_spoilages(
    db: Session,
    daily_record_id: Optional[int] = None
) -> SpoilageListResponse:
    """
    Get list of spoilage records, optionally filtered by daily_record_id.
    Uses eager loading to avoid N+1 queries.
    """
    query = db.query(Spoilage).options(joinedload(Spoilage.ingredient))

    if daily_record_id is not None:
        query = query.filter(Spoilage.daily_record_id == daily_record_id)

    spoilages = query.order_by(Spoilage.recorded_at.desc()).all()

    items = [
        _build_spoilage_response(spoilage, spoilage.ingredient)
        for spoilage in spoilages
        if spoilage.ingredient
    ]

    return SpoilageListResponse(items=items, total=len(items))


def get_spoilage_by_id(
    db: Session,
    spoilage_id: int
) -> tuple[Optional[SpoilageResponse], Optional[str]]:
    """
    Get a single spoilage record by ID.
    """
    spoilage = db.query(Spoilage).filter(Spoilage.id == spoilage_id).first()
    if not spoilage:
        return None, t("errors.spoilage_not_found")

    ingredient = db.query(Ingredient).filter(Ingredient.id == spoilage.ingredient_id).first()
    if not ingredient:
        return None, t("errors.ingredient_not_found")

    return _build_spoilage_response(spoilage, ingredient), None


def delete_spoilage(
    db: Session,
    spoilage_id: int
) -> tuple[bool, Optional[str]]:
    """
    Delete a spoilage record.
    Can only delete from an open day.

    Returns:
        Tuple of (success, error_message).
    """
    spoilage = db.query(Spoilage).filter(Spoilage.id == spoilage_id).first()
    if not spoilage:
        return False, t("errors.spoilage_not_found")

    # Validate daily record is still open
    daily_record = db.query(DailyRecord).filter(DailyRecord.id == spoilage.daily_record_id).first()
    if daily_record and daily_record.status != DayStatus.OPEN:
        return False, t("errors.cannot_delete_spoilage_closed")

    db.delete(spoilage)
    db.commit()

    return True, None


def _build_spoilage_response(spoilage: Spoilage, ingredient: Ingredient) -> SpoilageResponse:
    """Build response schema from spoilage model."""
    # Get Polish label for reason
    try:
        reason_enum = SpoilageReasonEnum(spoilage.reason.value)
        reason_label = SPOILAGE_REASON_LABELS.get(reason_enum, spoilage.reason.value)
    except (ValueError, AttributeError):
        reason_label = str(spoilage.reason)

    return SpoilageResponse(
        id=spoilage.id,
        daily_record_id=spoilage.daily_record_id,
        ingredient_id=spoilage.ingredient_id,
        ingredient_name=ingredient.name,
        unit_label=ingredient.unit_label or "szt",
        quantity=Decimal(str(spoilage.quantity)),
        reason=spoilage.reason.value if hasattr(spoilage.reason, 'value') else str(spoilage.reason),
        reason_label=reason_label,
        notes=spoilage.notes,
        recorded_at=spoilage.recorded_at,
        created_at=spoilage.created_at,
    )
