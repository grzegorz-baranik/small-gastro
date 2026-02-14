"""
Inventory Service

Handles inventory snapshot operations and discrepancy calculations.
Updated to use unified quantity field and include mid-day events
(deliveries, transfers, spoilage) in calculations.
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from typing import Optional, List
from decimal import Decimal
from app.models.inventory_snapshot import InventorySnapshot, SnapshotType, InventoryLocation
from app.models.ingredient import Ingredient, UnitType
from app.models.ingredient_batch import IngredientBatch
from app.models.daily_record import DailyRecord, DayStatus
from app.models.product import ProductIngredient
from app.models.sales_item import SalesItem
from app.models.delivery import Delivery, DeliveryItem
from app.models.storage_transfer import StorageTransfer
from app.models.spoilage import Spoilage
from app.models.storage_inventory import StorageInventory
from datetime import datetime
from app.schemas.inventory import (
    InventorySnapshotCreate,
    InventorySnapshotResponse,
    InventoryDiscrepancy,
    CurrentStock,
    IngredientAvailability,
    TransferStockItem,
    StockLevel,
    AdjustmentType,
    StockAdjustmentCreate,
    StockAdjustmentResponse,
)


# Discrepancy alert thresholds (as percentages)
# These could be moved to environment variables or config for different environments
DISCREPANCY_THRESHOLD_OK = Decimal("5")        # < 5% is OK (green)
DISCREPANCY_THRESHOLD_WARNING = Decimal("10")  # 5-10% is warning (yellow), > 10% is critical (red)


def get_snapshots_for_day(db: Session, daily_record_id: int) -> list[InventorySnapshot]:
    """Get all inventory snapshots for a daily record with eager loaded ingredients."""
    return db.query(InventorySnapshot).options(
        joinedload(InventorySnapshot.ingredient)
    ).filter(
        InventorySnapshot.daily_record_id == daily_record_id
    ).all()


def create_snapshot(
    db: Session,
    daily_record_id: int,
    snapshot_type: SnapshotType,
    data: InventorySnapshotCreate,
    location: InventoryLocation = InventoryLocation.SHOP
) -> InventorySnapshot:
    """
    Create an inventory snapshot.

    Supports both legacy (quantity_grams/quantity_count) and unified (quantity) fields.
    """
    # Get unified quantity
    quantity = data.get_unified_quantity()

    db_snap = InventorySnapshot(
        daily_record_id=daily_record_id,
        ingredient_id=data.ingredient_id,
        snapshot_type=snapshot_type,
        location=location,
        quantity=quantity,
    )
    db.add(db_snap)
    db.commit()
    db.refresh(db_snap)
    return db_snap


def get_mid_day_quantities(
    db: Session,
    daily_record_id: int,
    ingredient_id: int
) -> tuple[Decimal, Decimal, Decimal]:
    """
    Get total deliveries, transfers, and spoilage for an ingredient on a day.

    Returns (deliveries_total, transfers_total, spoilage_total).
    """
    # Sum deliveries (join through DeliveryItem since Delivery has multi-item structure)
    deliveries_sum = db.query(func.coalesce(func.sum(DeliveryItem.quantity), 0)).join(
        Delivery, DeliveryItem.delivery_id == Delivery.id
    ).filter(
        Delivery.daily_record_id == daily_record_id,
        DeliveryItem.ingredient_id == ingredient_id
    ).scalar()

    # Sum transfers
    transfers_sum = db.query(func.coalesce(func.sum(StorageTransfer.quantity), 0)).filter(
        StorageTransfer.daily_record_id == daily_record_id,
        StorageTransfer.ingredient_id == ingredient_id
    ).scalar()

    # Sum spoilage
    spoilage_sum = db.query(func.coalesce(func.sum(Spoilage.quantity), 0)).filter(
        Spoilage.daily_record_id == daily_record_id,
        Spoilage.ingredient_id == ingredient_id
    ).scalar()

    return (
        Decimal(str(deliveries_sum)),
        Decimal(str(transfers_sum)),
        Decimal(str(spoilage_sum))
    )


def calculate_discrepancies(db: Session, daily_record_id: int) -> list[InventoryDiscrepancy]:
    """
    Calculate discrepancies between expected and actual ingredient usage.

    For each ingredient:
    - actual_used = opening + deliveries + transfers - spoilage - closing
    - expected_used = SUM(product_sold * ingredient_quantity_per_product)
    - discrepancy = actual_used - expected_used
    """
    discrepancies = []

    # Get all active ingredients
    ingredients = db.query(Ingredient).filter(Ingredient.is_active == True).all()

    for ingredient in ingredients:
        # Get opening snapshot
        opening = db.query(InventorySnapshot).filter(
            InventorySnapshot.daily_record_id == daily_record_id,
            InventorySnapshot.ingredient_id == ingredient.id,
            InventorySnapshot.snapshot_type == SnapshotType.OPEN,
            InventorySnapshot.location == InventoryLocation.SHOP
        ).first()

        # Get closing snapshot
        closing = db.query(InventorySnapshot).filter(
            InventorySnapshot.daily_record_id == daily_record_id,
            InventorySnapshot.ingredient_id == ingredient.id,
            InventorySnapshot.snapshot_type == SnapshotType.CLOSE,
            InventorySnapshot.location == InventoryLocation.SHOP
        ).first()

        if not opening or not closing:
            continue

        # Use unified quantity field with null safety
        if opening.quantity is None or closing.quantity is None:
            continue

        opening_qty = Decimal(str(opening.quantity))
        closing_qty = Decimal(str(closing.quantity))

        # Get mid-day quantities
        deliveries, transfers, spoilage = get_mid_day_quantities(
            db, daily_record_id, ingredient.id
        )

        # Calculate actual usage: Opening + Deliveries + Transfers - Spoilage - Closing
        actual_used = opening_qty + deliveries + transfers - spoilage - closing_qty

        # Calculate expected usage based on sales
        # Get all sales for this day that use this ingredient
        expected_used = Decimal("0")

        sales_with_ingredient = db.query(
            SalesItem.quantity_sold,
            ProductIngredient.quantity
        ).join(
            ProductIngredient, SalesItem.product_id == ProductIngredient.product_variant_id
        ).filter(
            SalesItem.daily_record_id == daily_record_id,
            ProductIngredient.ingredient_id == ingredient.id
        ).all()

        for sale in sales_with_ingredient:
            if sale.quantity_sold is not None and sale.quantity is not None:
                expected_used += Decimal(str(sale.quantity_sold)) * Decimal(str(sale.quantity))

        discrepancy = actual_used - expected_used

        # Calculate percentage if expected > 0
        discrepancy_percent = None
        alert_level = "ok"

        if expected_used > 0:
            discrepancy_percent = abs((discrepancy / expected_used) * 100)

            if discrepancy_percent >= DISCREPANCY_THRESHOLD_WARNING:
                alert_level = "critical"
            elif discrepancy_percent >= DISCREPANCY_THRESHOLD_OK:
                alert_level = "warning"

        discrepancies.append(InventoryDiscrepancy(
            ingredient_id=ingredient.id,
            ingredient_name=ingredient.name,
            unit_type=ingredient.unit_type.value,
            unit_label=ingredient.unit_label or "szt",
            opening_quantity=opening_qty,
            closing_quantity=closing_qty,
            deliveries=deliveries,
            transfers=transfers,
            spoilage=spoilage,
            actual_used=actual_used,
            expected_used=expected_used,
            discrepancy=discrepancy,
            discrepancy_percent=discrepancy_percent,
            alert_level=alert_level,
        ))

    return discrepancies


def get_current_stock(db: Session) -> list[CurrentStock]:
    """Get current stock levels for all active ingredients."""
    ingredients = db.query(Ingredient).filter(Ingredient.is_active == True).all()

    return [
        CurrentStock(
            ingredient_id=ing.id,
            ingredient_name=ing.name,
            unit_type=ing.unit_type.value,
            unit_label=ing.unit_label or "szt",
            current_stock=Decimal(str(ing.current_stock_grams))
                if ing.unit_type == UnitType.WEIGHT
                else Decimal(str(ing.current_stock_count))
        )
        for ing in ingredients
    ]


def get_ingredient_availability(
    db: Session,
    daily_record_id: int,
    ingredient_id: int
) -> Optional[IngredientAvailability]:
    """
    Get availability status for an ingredient on a given day.

    Shows opening stock and what's available after mid-day events.
    """
    # Get ingredient
    ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not ingredient:
        return None

    # Get opening snapshot
    opening = db.query(InventorySnapshot).filter(
        InventorySnapshot.daily_record_id == daily_record_id,
        InventorySnapshot.ingredient_id == ingredient_id,
        InventorySnapshot.snapshot_type == SnapshotType.OPEN,
        InventorySnapshot.location == InventoryLocation.SHOP
    ).first()

    if not opening:
        return None

    opening_qty = Decimal(str(opening.quantity))

    # Get mid-day quantities
    deliveries, transfers, spoilage = get_mid_day_quantities(
        db, daily_record_id, ingredient_id
    )

    # Calculate available
    available = opening_qty + deliveries + transfers - spoilage

    return IngredientAvailability(
        ingredient_id=ingredient.id,
        ingredient_name=ingredient.name,
        unit_label=ingredient.unit_label or "szt",
        opening=opening_qty,
        deliveries=deliveries,
        transfers=transfers,
        spoilage=spoilage,
        available=available,
    )


def get_transfer_stock_info(
    db: Session,
    daily_record_id: int
) -> list[TransferStockItem]:
    """
    Get stock information for all ingredients showing both storage and shop quantities.

    Used in TransferModal to help users decide how much to transfer.
    Shop quantity = opening + deliveries + transfers - spoilage
    Storage quantity = current storage inventory
    """
    # Get all active ingredients with storage inventory
    ingredients = db.query(Ingredient).options(
        joinedload(Ingredient.storage_inventory)
    ).filter(Ingredient.is_active == True).all()

    result = []

    for ingredient in ingredients:
        # Get opening snapshot for shop quantity
        opening = db.query(InventorySnapshot).filter(
            InventorySnapshot.daily_record_id == daily_record_id,
            InventorySnapshot.ingredient_id == ingredient.id,
            InventorySnapshot.snapshot_type == SnapshotType.OPEN,
            InventorySnapshot.location == InventoryLocation.SHOP
        ).first()

        # Calculate shop quantity (opening + events)
        if opening and opening.quantity is not None:
            opening_qty = Decimal(str(opening.quantity))
            deliveries, transfers, spoilage = get_mid_day_quantities(
                db, daily_record_id, ingredient.id
            )
            shop_quantity = opening_qty + deliveries + transfers - spoilage
        else:
            shop_quantity = Decimal("0")

        # Get storage quantity
        storage_quantity = Decimal("0")
        if ingredient.storage_inventory:
            storage_quantity = Decimal(str(ingredient.storage_inventory.quantity))

        result.append(TransferStockItem(
            ingredient_id=ingredient.id,
            ingredient_name=ingredient.name,
            unit_type=ingredient.unit_type.value,
            unit_label=ingredient.unit_label or "szt",
            storage_quantity=storage_quantity,
            shop_quantity=shop_quantity,
        ))

    return result


def get_stock_levels(db: Session) -> List[StockLevel]:
    """
    Get current stock levels for all ingredients, showing warehouse and shop quantities.

    Logic:
    1. Get all active ingredients
    2. For each ingredient:
       - warehouse_qty: from StorageInventory table
       - shop_qty: from latest opening InventorySnapshot for the current/most recent open day
       - batches_count: count of IngredientBatch records for this ingredient where remaining_quantity > 0
       - nearest_expiry: min expiry_date from IngredientBatch where remaining_quantity > 0
    3. Return combined list
    """
    # Get the most recent DailyRecord (prefer OPEN, fallback to latest CLOSED)
    current_day = db.query(DailyRecord).filter(
        DailyRecord.status == DayStatus.OPEN
    ).order_by(desc(DailyRecord.date)).first()

    if not current_day:
        # Fallback to most recent closed day
        current_day = db.query(DailyRecord).filter(
            DailyRecord.status == DayStatus.CLOSED
        ).order_by(desc(DailyRecord.date)).first()

    # Get all active ingredients with storage inventory eager loaded
    ingredients = db.query(Ingredient).options(
        joinedload(Ingredient.storage_inventory)
    ).filter(Ingredient.is_active == True).all()

    result = []

    for ingredient in ingredients:
        # Get warehouse quantity from StorageInventory
        warehouse_qty = Decimal("0")
        if ingredient.storage_inventory:
            warehouse_qty = Decimal(str(ingredient.storage_inventory.quantity))

        # Get shop quantity from opening snapshot of current/most recent day
        shop_qty = Decimal("0")
        if current_day:
            opening_snapshot = db.query(InventorySnapshot).filter(
                InventorySnapshot.daily_record_id == current_day.id,
                InventorySnapshot.ingredient_id == ingredient.id,
                InventorySnapshot.snapshot_type == SnapshotType.OPEN,
                InventorySnapshot.location == InventoryLocation.SHOP
            ).first()

            if opening_snapshot and opening_snapshot.quantity is not None:
                shop_qty = Decimal(str(opening_snapshot.quantity))

        # Calculate total
        total_qty = warehouse_qty + shop_qty

        # Get batch information (count of active batches and nearest expiry)
        batches_count = db.query(func.count(IngredientBatch.id)).filter(
            IngredientBatch.ingredient_id == ingredient.id,
            IngredientBatch.remaining_quantity > 0,
            IngredientBatch.is_active == True
        ).scalar() or 0

        # Get nearest expiry date from active batches
        nearest_expiry = db.query(func.min(IngredientBatch.expiry_date)).filter(
            IngredientBatch.ingredient_id == ingredient.id,
            IngredientBatch.remaining_quantity > 0,
            IngredientBatch.is_active == True,
            IngredientBatch.expiry_date.isnot(None)
        ).scalar()

        result.append(StockLevel(
            ingredient_id=ingredient.id,
            ingredient_name=ingredient.name,
            unit_type=ingredient.unit_type.value,
            unit_label=ingredient.unit_label or "szt",
            warehouse_qty=warehouse_qty,
            shop_qty=shop_qty,
            total_qty=total_qty,
            batches_count=batches_count,
            nearest_expiry=nearest_expiry,
        ))

    return result


class IngredientNotFoundError(Exception):
    """Raised when ingredient is not found."""
    pass


class ShopAdjustmentNotSupportedError(Exception):
    """Raised when shop adjustment is attempted (not yet supported)."""
    pass


class InsufficientStockError(Exception):
    """Raised when there is not enough stock for subtraction."""
    def __init__(self, available: Decimal):
        self.available = available
        super().__init__(f"Insufficient stock (available: {available})")


def create_stock_adjustment(
    db: Session,
    adjustment: StockAdjustmentCreate
) -> StockAdjustmentResponse:
    """
    Create a stock adjustment for warehouse (storage) inventory.

    For 'storage': Updates StorageInventory table directly.
    For 'shop': Not yet supported (shop inventory is snapshot-based).

    Steps:
    1. Get current quantity for the ingredient at the location
    2. Calculate new quantity based on adjustment_type (set/add/subtract)
    3. Update the appropriate table
    4. Return response with before/after quantities

    Raises:
        IngredientNotFoundError: If ingredient does not exist
        ShopAdjustmentNotSupportedError: If location is 'shop'
        InsufficientStockError: If subtract would result in negative stock
    """
    # Get ingredient
    ingredient = db.query(Ingredient).filter(Ingredient.id == adjustment.ingredient_id).first()
    if not ingredient:
        raise IngredientNotFoundError()

    # Shop adjustments not supported yet (shop inventory is snapshot-based)
    if adjustment.location == "shop":
        raise ShopAdjustmentNotSupportedError()

    # Get or create StorageInventory record
    storage_inv = db.query(StorageInventory).filter(
        StorageInventory.ingredient_id == adjustment.ingredient_id
    ).first()

    if not storage_inv:
        # Create new storage inventory record with 0 quantity
        storage_inv = StorageInventory(
            ingredient_id=adjustment.ingredient_id,
            quantity=Decimal("0")
        )
        db.add(storage_inv)
        db.flush()  # Get the ID without committing

    previous_quantity = Decimal(str(storage_inv.quantity))

    # Calculate new quantity based on adjustment type
    if adjustment.adjustment_type == AdjustmentType.set:
        new_quantity = adjustment.quantity
        adjustment_amount = new_quantity - previous_quantity
    elif adjustment.adjustment_type == AdjustmentType.add:
        new_quantity = previous_quantity + adjustment.quantity
        adjustment_amount = adjustment.quantity
    elif adjustment.adjustment_type == AdjustmentType.subtract:
        new_quantity = previous_quantity - adjustment.quantity
        adjustment_amount = -adjustment.quantity
        # Check for negative stock
        if new_quantity < 0:
            raise InsufficientStockError(previous_quantity)
    else:
        # Should not happen due to Pydantic validation
        raise ValueError(f"Invalid adjustment type: {adjustment.adjustment_type}")

    # Update storage inventory
    storage_inv.quantity = new_quantity
    storage_inv.last_counted_at = datetime.now()
    db.commit()
    db.refresh(storage_inv)

    return StockAdjustmentResponse(
        id=storage_inv.id,
        ingredient_id=ingredient.id,
        ingredient_name=ingredient.name,
        location=adjustment.location,
        adjustment_type=adjustment.adjustment_type.value,
        previous_quantity=previous_quantity,
        new_quantity=new_quantity,
        adjustment_amount=adjustment_amount,
        reason=adjustment.reason,
        notes=adjustment.notes,
        created_at=storage_inv.updated_at or datetime.now(),
    )
