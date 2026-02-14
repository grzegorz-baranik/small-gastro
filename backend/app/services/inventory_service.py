"""
Inventory Service

Handles inventory snapshot operations and discrepancy calculations.
Updated to use unified quantity field and include mid-day events
(deliveries, transfers, spoilage) in calculations.
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional
from decimal import Decimal
from app.models.inventory_snapshot import InventorySnapshot, SnapshotType, InventoryLocation
from app.models.ingredient import Ingredient, UnitType
from app.models.product import ProductIngredient
from app.models.sales_item import SalesItem
from app.models.delivery import Delivery, DeliveryItem
from app.models.storage_transfer import StorageTransfer
from app.models.spoilage import Spoilage
from app.models.storage_inventory import StorageInventory
from app.schemas.inventory import (
    InventorySnapshotCreate,
    InventorySnapshotResponse,
    InventoryDiscrepancy,
    CurrentStock,
    IngredientAvailability,
    TransferStockItem,
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
