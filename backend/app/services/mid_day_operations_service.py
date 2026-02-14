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
from app.models.delivery import Delivery, DeliveryItem
from app.models.storage_transfer import StorageTransfer
from app.models.spoilage import Spoilage, SpoilageReason
from app.models.storage_inventory import StorageInventory
from app.models.transaction import Transaction, TransactionType, PaymentMethod
from app.models.ingredient_batch import IngredientBatch, BatchLocation

from app.services import batch_service

from app.schemas.mid_day_operations import (
    DeliveryCreate,
    DeliveryResponse,
    DeliveryListResponse,
    DeliveryItemResponse,
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
# Delivery CRUD (Multi-item structure)
# -----------------------------------------------------------------------------

def create_delivery(
    db: Session,
    data: DeliveryCreate
) -> tuple[Optional[DeliveryResponse], Optional[str]]:
    """
    Create a new multi-item delivery record with auto-expense transaction.

    Returns:
        Tuple of (response, error_message). If error_message is not None, operation failed.
    """
    # Validate daily record
    daily_record, error = _validate_daily_record_open(db, data.daily_record_id)
    if error:
        return None, error

    # Validate all ingredients upfront
    ingredients_map: dict[int, Ingredient] = {}
    for item in data.items:
        ingredient, error = _validate_ingredient_active(db, item.ingredient_id)
        if error:
            return None, error
        ingredients_map[item.ingredient_id] = ingredient

    try:
        # Create expense transaction for the delivery
        transaction_description = t("labels.delivery_expense")
        if data.supplier_name:
            transaction_description = f"{transaction_description} - {data.supplier_name}"
        if data.invoice_number:
            transaction_description = f"{transaction_description} ({data.invoice_number})"

        db_transaction = Transaction(
            type=TransactionType.EXPENSE,
            category_id=None,  # Optional - admin can categorize later
            amount=data.total_cost_pln,
            payment_method=PaymentMethod.CASH,  # Default, can be changed later
            description=transaction_description,
            transaction_date=daily_record.date,
            daily_record_id=data.daily_record_id,
        )
        db.add(db_transaction)
        db.flush()  # Get transaction ID without committing

        # Determine destination location for batches (default to storage)
        destination_str = data.destination or "storage"
        batch_location = BatchLocation(destination_str)

        # Create delivery
        db_delivery = Delivery(
            daily_record_id=data.daily_record_id,
            supplier_name=data.supplier_name,
            invoice_number=data.invoice_number,
            total_cost_pln=data.total_cost_pln,
            destination=batch_location,
            notes=data.notes,
            transaction_id=db_transaction.id,
            delivered_at=data.delivered_at or datetime.now(),
        )
        db.add(db_delivery)
        db.flush()  # Get delivery ID

        # Create delivery items and batches
        for item_data in data.items:
            db_item = DeliveryItem(
                delivery_id=db_delivery.id,
                ingredient_id=item_data.ingredient_id,
                quantity=item_data.quantity,
                cost_pln=item_data.cost_pln,
                expiry_date=item_data.expiry_date,
            )
            db.add(db_item)
            db.flush()  # Get item ID for batch creation

            # Auto-create batch for tracking at the specified destination
            batch_service.create_batch_from_delivery_item(db, db_item, location=destination_str)

        db.commit()
        db.refresh(db_delivery)

        return _build_delivery_response(db, db_delivery, ingredients_map), None
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Blad integralnosci bazy danych przy tworzeniu dostawy: {e}")
        return None, t("errors.database_integrity_error")


def get_deliveries(
    db: Session,
    daily_record_id: Optional[int] = None
) -> DeliveryListResponse:
    """
    Get list of deliveries with items, optionally filtered by daily_record_id.
    Uses eager loading to avoid N+1 queries.
    """
    query = db.query(Delivery).options(
        joinedload(Delivery.items).joinedload(DeliveryItem.ingredient),
        joinedload(Delivery.items).joinedload(DeliveryItem.batch)
    )

    if daily_record_id is not None:
        query = query.filter(Delivery.daily_record_id == daily_record_id)

    deliveries = query.order_by(Delivery.delivered_at.desc()).all()

    result_items = []
    for delivery in deliveries:
        # Build ingredients map from loaded items
        ingredients_map = {
            item.ingredient_id: item.ingredient
            for item in delivery.items
            if item.ingredient
        }
        result_items.append(_build_delivery_response(db, delivery, ingredients_map))

    return DeliveryListResponse(items=result_items, total=len(result_items))


def get_delivery_by_id(
    db: Session,
    delivery_id: int
) -> tuple[Optional[DeliveryResponse], Optional[str]]:
    """
    Get a single delivery by ID with all items.
    """
    delivery = db.query(Delivery).options(
        joinedload(Delivery.items).joinedload(DeliveryItem.ingredient),
        joinedload(Delivery.items).joinedload(DeliveryItem.batch)
    ).filter(Delivery.id == delivery_id).first()

    if not delivery:
        return None, t("errors.delivery_not_found")

    # Build ingredients map from loaded items
    ingredients_map = {
        item.ingredient_id: item.ingredient
        for item in delivery.items
        if item.ingredient
    }

    return _build_delivery_response(db, delivery, ingredients_map), None


def delete_delivery(
    db: Session,
    delivery_id: int
) -> tuple[bool, Optional[str]]:
    """
    Delete a delivery record and its associated transaction.
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

    # Delete associated transaction if exists
    if delivery.transaction_id:
        transaction = db.query(Transaction).filter(Transaction.id == delivery.transaction_id).first()
        if transaction:
            db.delete(transaction)

    # Delete delivery (items cascade automatically)
    db.delete(delivery)
    db.commit()

    return True, None


def _build_delivery_item_response(item: DeliveryItem, ingredient: Ingredient) -> DeliveryItemResponse:
    """Build response schema for a single delivery item."""
    # Get batch info if available
    batch_id = None
    batch_number = None
    if hasattr(item, 'batch') and item.batch:
        batch_id = item.batch.id
        batch_number = item.batch.batch_number

    return DeliveryItemResponse(
        id=item.id,
        delivery_id=item.delivery_id,
        ingredient_id=item.ingredient_id,
        ingredient_name=ingredient.name,
        unit_label=ingredient.unit_label or "szt",
        quantity=Decimal(str(item.quantity)),
        cost_pln=Decimal(str(item.cost_pln)) if item.cost_pln else None,
        expiry_date=item.expiry_date,
        batch_id=batch_id,
        batch_number=batch_number,
        created_at=item.created_at,
    )


def _build_delivery_response(
    db: Session,
    delivery: Delivery,
    ingredients_map: dict[int, Ingredient]
) -> DeliveryResponse:
    """Build response schema from delivery model with all items."""
    # Build items responses
    items_responses = []
    for item in delivery.items:
        ingredient = ingredients_map.get(item.ingredient_id)
        if ingredient:
            items_responses.append(_build_delivery_item_response(item, ingredient))

    # Get destination as string value
    destination_value = "storage"
    if delivery.destination:
        destination_value = delivery.destination.value if hasattr(delivery.destination, 'value') else str(delivery.destination)

    return DeliveryResponse(
        id=delivery.id,
        daily_record_id=delivery.daily_record_id,
        supplier_name=delivery.supplier_name,
        invoice_number=delivery.invoice_number,
        total_cost_pln=Decimal(str(delivery.total_cost_pln)),
        destination=destination_value,
        notes=delivery.notes,
        transaction_id=delivery.transaction_id,
        items=items_responses,
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

    If batch_id is provided, also deducts from the batch.

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

    # Validate batch if provided
    batch = None
    if data.batch_id:
        batch = db.query(IngredientBatch).filter(IngredientBatch.id == data.batch_id).first()
        if not batch:
            return None, t("errors.batch_not_found")
        if batch.ingredient_id != data.ingredient_id:
            return None, t("errors.batch_ingredient_mismatch")

    # Convert schema enum to model enum
    reason_value = SpoilageReason(data.reason.value)

    try:
        # Create spoilage
        db_spoilage = Spoilage(
            daily_record_id=data.daily_record_id,
            ingredient_id=data.ingredient_id,
            batch_id=data.batch_id,
            quantity=data.quantity,
            reason=reason_value,
            notes=data.notes,
            recorded_at=data.recorded_at or datetime.now(),
        )
        db.add(db_spoilage)
        db.flush()  # Get spoilage ID

        # Deduct from batch if provided
        if data.batch_id:
            _, batch_error = batch_service.deduct_from_batch(
                db=db,
                batch_id=data.batch_id,
                quantity=Decimal(str(data.quantity)),
                reason="spoilage",
                daily_record_id=data.daily_record_id,
                reference_type="spoilage",
                reference_id=db_spoilage.id,
                notes=f"Strata: {reason_value.value}"
            )
            if batch_error:
                db.rollback()
                return None, batch_error

        db.commit()
        db.refresh(db_spoilage)

        return _build_spoilage_response(db_spoilage, ingredient, batch), None
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
    query = db.query(Spoilage).options(
        joinedload(Spoilage.ingredient),
        joinedload(Spoilage.batch)
    )

    if daily_record_id is not None:
        query = query.filter(Spoilage.daily_record_id == daily_record_id)

    spoilages = query.order_by(Spoilage.recorded_at.desc()).all()

    items = [
        _build_spoilage_response(spoilage, spoilage.ingredient, spoilage.batch)
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
    spoilage = db.query(Spoilage).options(
        joinedload(Spoilage.ingredient),
        joinedload(Spoilage.batch)
    ).filter(Spoilage.id == spoilage_id).first()
    if not spoilage:
        return None, t("errors.spoilage_not_found")

    if not spoilage.ingredient:
        return None, t("errors.ingredient_not_found")

    return _build_spoilage_response(spoilage, spoilage.ingredient, spoilage.batch), None


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


def _build_spoilage_response(
    spoilage: Spoilage,
    ingredient: Ingredient,
    batch: Optional[IngredientBatch] = None
) -> SpoilageResponse:
    """Build response schema from spoilage model."""
    # Get Polish label for reason
    try:
        reason_enum = SpoilageReasonEnum(spoilage.reason.value)
        reason_label = SPOILAGE_REASON_LABELS.get(reason_enum, spoilage.reason.value)
    except (ValueError, AttributeError):
        reason_label = str(spoilage.reason)

    # Get batch info
    batch_id = None
    batch_number = None
    if batch:
        batch_id = batch.id
        batch_number = batch.batch_number

    return SpoilageResponse(
        id=spoilage.id,
        daily_record_id=spoilage.daily_record_id,
        ingredient_id=spoilage.ingredient_id,
        ingredient_name=ingredient.name,
        unit_label=ingredient.unit_label or "szt",
        quantity=Decimal(str(spoilage.quantity)),
        reason=spoilage.reason.value if hasattr(spoilage.reason, 'value') else str(spoilage.reason),
        reason_label=reason_label,
        batch_id=batch_id,
        batch_number=batch_number,
        notes=spoilage.notes,
        recorded_at=spoilage.recorded_at,
        created_at=spoilage.created_at,
    )
