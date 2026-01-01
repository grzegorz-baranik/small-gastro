from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.inventory import (
    InventorySnapshotCreate,
    InventorySnapshotResponse,
    InventoryDiscrepancy,
    CurrentStock,
)
from app.models.inventory_snapshot import SnapshotType
from app.services import inventory_service

router = APIRouter()


@router.get("/current", response_model=list[CurrentStock])
def get_current_stock(
    db: Session = Depends(get_db),
):
    """Pobierz aktualny stan magazynowy."""
    return inventory_service.get_current_stock(db)


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
            quantity_grams=s.quantity_grams,
            quantity_count=s.quantity_count,
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
    snapshot = inventory_service.create_snapshot(db, daily_record_id, snapshot_type, data)
    return InventorySnapshotResponse(
        id=snapshot.id,
        daily_record_id=snapshot.daily_record_id,
        ingredient_id=snapshot.ingredient_id,
        ingredient_name=snapshot.ingredient.name if snapshot.ingredient else None,
        snapshot_type=snapshot.snapshot_type,
        quantity_grams=snapshot.quantity_grams,
        quantity_count=snapshot.quantity_count,
        recorded_at=snapshot.recorded_at,
    )
