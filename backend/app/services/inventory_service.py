from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from decimal import Decimal
from app.models.inventory_snapshot import InventorySnapshot, SnapshotType
from app.models.ingredient import Ingredient, UnitType
from app.models.product import ProductIngredient
from app.models.sales_item import SalesItem
from app.schemas.inventory import InventorySnapshotCreate, InventorySnapshotResponse, InventoryDiscrepancy, CurrentStock


def get_snapshots_for_day(db: Session, daily_record_id: int) -> list[InventorySnapshot]:
    return db.query(InventorySnapshot).filter(
        InventorySnapshot.daily_record_id == daily_record_id
    ).all()


def create_snapshot(
    db: Session,
    daily_record_id: int,
    snapshot_type: SnapshotType,
    data: InventorySnapshotCreate
) -> InventorySnapshot:
    db_snap = InventorySnapshot(
        daily_record_id=daily_record_id,
        ingredient_id=data.ingredient_id,
        snapshot_type=snapshot_type,
        quantity_grams=data.quantity_grams,
        quantity_count=data.quantity_count,
    )
    db.add(db_snap)
    db.commit()
    db.refresh(db_snap)
    return db_snap


def calculate_discrepancies(db: Session, daily_record_id: int) -> list[InventoryDiscrepancy]:
    """
    Calculate discrepancies between expected and actual ingredient usage.

    For each ingredient:
    - actual_used = opening_snapshot - closing_snapshot
    - expected_used = SUM(product_sold * ingredient_quantity_per_product)
    - discrepancy = actual_used - expected_used
    """
    discrepancies = []

    # Get all ingredients
    ingredients = db.query(Ingredient).all()

    for ingredient in ingredients:
        # Get opening and closing snapshots
        opening = db.query(InventorySnapshot).filter(
            InventorySnapshot.daily_record_id == daily_record_id,
            InventorySnapshot.ingredient_id == ingredient.id,
            InventorySnapshot.snapshot_type == SnapshotType.OPEN
        ).first()

        closing = db.query(InventorySnapshot).filter(
            InventorySnapshot.daily_record_id == daily_record_id,
            InventorySnapshot.ingredient_id == ingredient.id,
            InventorySnapshot.snapshot_type == SnapshotType.CLOSE
        ).first()

        if not opening or not closing:
            continue

        # Calculate actual used
        if ingredient.unit_type == UnitType.WEIGHT:
            opening_qty = Decimal(str(opening.quantity_grams or 0))
            closing_qty = Decimal(str(closing.quantity_grams or 0))
        else:
            opening_qty = Decimal(str(opening.quantity_count or 0))
            closing_qty = Decimal(str(closing.quantity_count or 0))

        actual_used = opening_qty - closing_qty

        # Calculate expected usage based on sales
        # Get all sales for this day that use this ingredient
        expected_used = Decimal("0")

        sales_with_ingredient = db.query(
            SalesItem.quantity_sold,
            ProductIngredient.quantity
        ).join(
            ProductIngredient, SalesItem.product_id == ProductIngredient.product_id
        ).filter(
            SalesItem.daily_record_id == daily_record_id,
            ProductIngredient.ingredient_id == ingredient.id
        ).all()

        for sale in sales_with_ingredient:
            expected_used += Decimal(str(sale.quantity_sold)) * Decimal(str(sale.quantity))

        discrepancy = actual_used - expected_used

        # Calculate percentage if expected > 0
        discrepancy_percent = None
        if expected_used > 0:
            discrepancy_percent = (discrepancy / expected_used) * 100

        discrepancies.append(InventoryDiscrepancy(
            ingredient_id=ingredient.id,
            ingredient_name=ingredient.name,
            unit_type=ingredient.unit_type.value,
            opening_quantity=opening_qty,
            closing_quantity=closing_qty,
            actual_used=actual_used,
            expected_used=expected_used,
            discrepancy=discrepancy,
            discrepancy_percent=discrepancy_percent,
        ))

    return discrepancies


def get_current_stock(db: Session) -> list[CurrentStock]:
    ingredients = db.query(Ingredient).all()

    return [
        CurrentStock(
            ingredient_id=ing.id,
            ingredient_name=ing.name,
            unit_type=ing.unit_type.value,
            current_stock=Decimal(str(ing.current_stock_grams))
                if ing.unit_type == UnitType.WEIGHT
                else Decimal(str(ing.current_stock_count))
        )
        for ing in ingredients
    ]
