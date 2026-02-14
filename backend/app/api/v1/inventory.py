"""
Inventory API - Snapshot and discrepancy endpoints.

Provides endpoints for managing inventory snapshots and calculating discrepancies.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal

from app.api.deps import get_db
from app.core.i18n import t
from app.schemas.inventory import (
    InventorySnapshotCreate,
    InventorySnapshotResponse,
    InventoryDiscrepancy,
    CurrentStock,
    IngredientAvailability,
    TransferStockItem,
    StockLevel,
    StockAdjustmentCreate,
    StockAdjustmentResponse,
)
from app.models.inventory_snapshot import SnapshotType, InventoryLocation
from app.services import inventory_service
from app.services.inventory_service import (
    IngredientNotFoundError,
    ShopAdjustmentNotSupportedError,
    InsufficientStockError,
)

router = APIRouter()


@router.get("/current", response_model=list[CurrentStock])
def get_current_stock(
    db: Session = Depends(get_db),
):
    """Pobierz aktualny stan magazynowy."""
    return inventory_service.get_current_stock(db)


@router.get("/stock-levels", response_model=list[StockLevel])
def get_stock_levels(
    db: Session = Depends(get_db),
):
    """
    Pobierz stany magazynowe dla wszystkich skladnikow (magazyn + sklep).

    Zwraca aktualne ilosci w magazynie i sklepie dla kazdego skladnika,
    wraz z informacjami o partiach i najbliższej dacie waznosci.
    """
    return inventory_service.get_stock_levels(db)


@router.get("/daily-record/{daily_record_id}/snapshots", response_model=list[InventorySnapshotResponse])
def get_snapshots_for_day(
    daily_record_id: int,
    db: Session = Depends(get_db),
):
    """Pobierz snapshoty inwentarza dla danego dnia."""
    snapshots = inventory_service.get_snapshots_for_day(db, daily_record_id)
    return [
        InventorySnapshotResponse(
            id=s.id,
            daily_record_id=s.daily_record_id,
            ingredient_id=s.ingredient_id,
            ingredient_name=s.ingredient.name if s.ingredient else None,
            snapshot_type=s.snapshot_type,
            location=s.location,
            quantity=Decimal(str(s.quantity)),
            # Legacy fields for backwards compatibility
            quantity_grams=Decimal(str(s.quantity)) if s.ingredient and s.ingredient.unit_type.value == "weight" else None,
            quantity_count=int(s.quantity) if s.ingredient and s.ingredient.unit_type.value == "count" else None,
            recorded_at=s.recorded_at,
        )
        for s in snapshots
    ]


@router.get("/discrepancies/{daily_record_id}", response_model=list[InventoryDiscrepancy])
def get_discrepancies(
    daily_record_id: int,
    db: Session = Depends(get_db),
):
    """Oblicz rozbieznosci inwentarza dla danego dnia."""
    return inventory_service.calculate_discrepancies(db, daily_record_id)


@router.post("/snapshot", response_model=InventorySnapshotResponse, status_code=status.HTTP_201_CREATED)
def create_snapshot(
    daily_record_id: int,
    snapshot_type: SnapshotType,
    data: InventorySnapshotCreate,
    db: Session = Depends(get_db),
):
    """Utworz snapshot inwentarza."""
    location = data.location if hasattr(data, 'location') else InventoryLocation.SHOP
    snapshot = inventory_service.create_snapshot(db, daily_record_id, snapshot_type, data, location)
    return InventorySnapshotResponse(
        id=snapshot.id,
        daily_record_id=snapshot.daily_record_id,
        ingredient_id=snapshot.ingredient_id,
        ingredient_name=snapshot.ingredient.name if snapshot.ingredient else None,
        snapshot_type=snapshot.snapshot_type,
        location=snapshot.location,
        quantity=Decimal(str(snapshot.quantity)),
        # Legacy fields for backwards compatibility
        quantity_grams=Decimal(str(snapshot.quantity)) if snapshot.ingredient and snapshot.ingredient.unit_type.value == "weight" else None,
        quantity_count=int(snapshot.quantity) if snapshot.ingredient and snapshot.ingredient.unit_type.value == "count" else None,
        recorded_at=snapshot.recorded_at,
    )


@router.get("/daily-record/{daily_record_id}/availability/{ingredient_id}", response_model=IngredientAvailability)
def get_ingredient_availability(
    daily_record_id: int,
    ingredient_id: int,
    db: Session = Depends(get_db),
):
    """
    Pobierz dostepnosc skladnika na dany dzien.

    Pokazuje stan poczatkowy plus/minus wydarzenia w ciagu dnia.
    """
    result = inventory_service.get_ingredient_availability(db, daily_record_id, ingredient_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.ingredient_or_record_not_found")
        )
    return result


@router.get("/daily-record/{daily_record_id}/transfer-stock", response_model=list[TransferStockItem])
def get_transfer_stock(
    daily_record_id: int,
    db: Session = Depends(get_db),
):
    """
    Pobierz stany magazynowe do transferu.

    Zwraca ilosci w magazynie i na sklepie dla wszystkich skladnikow.
    Uzywane w oknie dialogowym transferu aby pomoc uzytkownikom
    zdecydowac ile przenieść.
    """
    return inventory_service.get_transfer_stock_info(db, daily_record_id)


@router.post("/adjustment", response_model=StockAdjustmentResponse, status_code=status.HTTP_201_CREATED)
def create_adjustment(
    adjustment: StockAdjustmentCreate,
    db: Session = Depends(get_db),
):
    """
    Utworz korekte stanow magazynowych.

    Pozwala na korekte ilosci skladnikow w magazynie (storage).
    Korekty dla sklepu (shop) nie sa jeszcze obslugiwane.

    Typy korekty:
    - set: Ustaw dokladna wartosc
    - add: Dodaj ilosc
    - subtract: Odejmij ilosc
    """
    try:
        return inventory_service.create_stock_adjustment(db, adjustment)
    except IngredientNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.ingredient_not_found")
        )
    except ShopAdjustmentNotSupportedError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=t("errors.shop_adjustment_not_supported")
        )
    except InsufficientStockError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=t("errors.insufficient_storage", available=str(e.available))
        )
