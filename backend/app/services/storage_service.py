from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.models.storage_inventory import StorageInventory
from app.models.ingredient import Ingredient, UnitType
from app.schemas.storage import (
    StorageInventoryCreate,
    StorageCountItem,
    StorageCurrentStatus,
)


def get_storage_inventory(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    ingredient_id: Optional[int] = None,
) -> tuple[list[StorageInventory], int]:
    """Pobierz historie zliczen magazynowych."""
    query = db.query(StorageInventory).options(
        joinedload(StorageInventory.ingredient)
    )

    if ingredient_id:
        query = query.filter(StorageInventory.ingredient_id == ingredient_id)

    query = query.order_by(desc(StorageInventory.recorded_at))
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total


def get_storage_record(db: Session, record_id: int) -> Optional[StorageInventory]:
    """Pobierz pojedynczy rekord zliczenia."""
    return db.query(StorageInventory).options(
        joinedload(StorageInventory.ingredient)
    ).filter(StorageInventory.id == record_id).first()


def create_storage_count(
    db: Session,
    data: StorageInventoryCreate,
    recorded_by: Optional[str] = None
) -> Optional[StorageInventory]:
    """Zapisz zliczenie magazynowe dla skladnika."""
    # Verify ingredient exists
    ingredient = db.query(Ingredient).filter(Ingredient.id == data.ingredient_id).first()
    if not ingredient:
        return None

    db_record = StorageInventory(
        ingredient_id=data.ingredient_id,
        quantity_grams=data.quantity_grams,
        quantity_count=data.quantity_count,
        notes=data.notes,
        recorded_by=recorded_by,
    )
    db.add(db_record)

    # Also update the ingredient's current stock
    if ingredient.unit_type == UnitType.WEIGHT and data.quantity_grams is not None:
        ingredient.current_stock_grams = data.quantity_grams
    elif ingredient.unit_type == UnitType.COUNT and data.quantity_count is not None:
        ingredient.current_stock_count = data.quantity_count

    db.commit()
    db.refresh(db_record)
    return db_record


def create_storage_count_bulk(
    db: Session,
    items: list[StorageCountItem],
    notes: Optional[str] = None,
    recorded_by: Optional[str] = None
) -> list[StorageInventory]:
    """Zapisz zliczenie magazynowe dla wielu skladnikow naraz."""
    records = []
    recorded_at = datetime.utcnow()

    for item in items:
        ingredient = db.query(Ingredient).filter(Ingredient.id == item.ingredient_id).first()
        if not ingredient:
            continue

        db_record = StorageInventory(
            ingredient_id=item.ingredient_id,
            quantity_grams=item.quantity_grams,
            quantity_count=item.quantity_count,
            notes=notes,
            recorded_by=recorded_by,
            recorded_at=recorded_at,
        )
        db.add(db_record)
        records.append(db_record)

        # Update ingredient's current stock
        if ingredient.unit_type == UnitType.WEIGHT and item.quantity_grams is not None:
            ingredient.current_stock_grams = item.quantity_grams
        elif ingredient.unit_type == UnitType.COUNT and item.quantity_count is not None:
            ingredient.current_stock_count = item.quantity_count

    db.commit()
    for record in records:
        db.refresh(record)
    return records


def get_current_storage_status(
    db: Session,
    active_only: bool = True
) -> list[StorageCurrentStatus]:
    """Pobierz aktualny stan magazynowy wszystkich skladnikow."""
    query = db.query(Ingredient)

    if active_only:
        query = query.filter(Ingredient.is_active == True)

    ingredients = query.order_by(Ingredient.name).all()

    result = []
    for ing in ingredients:
        # Get last count date
        last_count = db.query(StorageInventory.recorded_at).filter(
            StorageInventory.ingredient_id == ing.id
        ).order_by(desc(StorageInventory.recorded_at)).first()

        if ing.unit_type == UnitType.WEIGHT:
            current_qty = Decimal(str(ing.current_stock_grams or 0))
        else:
            current_qty = Decimal(str(ing.current_stock_count or 0))

        result.append(StorageCurrentStatus(
            ingredient_id=ing.id,
            ingredient_name=ing.name,
            ingredient_unit_type=ing.unit_type.value,
            ingredient_unit_label=getattr(ing, 'unit_label', None),
            current_quantity=current_qty,
            last_count_at=last_count[0] if last_count else None,
            is_active=getattr(ing, 'is_active', True),
        ))

    return result


def get_latest_count_for_ingredient(
    db: Session,
    ingredient_id: int
) -> Optional[StorageInventory]:
    """Pobierz ostatnie zliczenie dla skladnika."""
    return db.query(StorageInventory).filter(
        StorageInventory.ingredient_id == ingredient_id
    ).order_by(desc(StorageInventory.recorded_at)).first()
