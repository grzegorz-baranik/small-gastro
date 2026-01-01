from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.api.deps import get_db
from app.schemas.storage import (
    StorageInventoryCreate,
    StorageInventoryResponse,
    StorageInventoryListResponse,
    StorageCountBulkCreate,
    StorageCountBulkResponse,
    StorageCurrentStatus,
)
from app.services import storage_service

router = APIRouter()


@router.get("/inventory", response_model=StorageInventoryListResponse)
def list_storage_inventory(
    skip: int = 0,
    limit: int = 100,
    ingredient_id: Optional[int] = Query(None, description="Filtruj po skladniku"),
    db: Session = Depends(get_db),
):
    """Pobierz historie zliczen magazynowych."""
    items, total = storage_service.get_storage_inventory(
        db, skip, limit, ingredient_id=ingredient_id
    )

    response_items = [
        StorageInventoryResponse(
            id=item.id,
            ingredient_id=item.ingredient_id,
            quantity_grams=item.quantity_grams,
            quantity_count=item.quantity_count,
            ingredient_name=item.ingredient.name if item.ingredient else None,
            ingredient_unit_type=item.ingredient.unit_type.value if item.ingredient else None,
            ingredient_unit_label=getattr(item.ingredient, 'unit_label', None) if item.ingredient else None,
            notes=item.notes,
            recorded_at=item.recorded_at,
            recorded_by=item.recorded_by,
        )
        for item in items
    ]

    return StorageInventoryListResponse(items=response_items, total=total)


@router.get("/current", response_model=list[StorageCurrentStatus])
def get_current_storage_status(
    active_only: bool = Query(True, description="Tylko aktywne skladniki"),
    db: Session = Depends(get_db),
):
    """Pobierz aktualny stan magazynowy wszystkich skladnikow."""
    return storage_service.get_current_storage_status(db, active_only=active_only)


@router.get("/inventory/{record_id}", response_model=StorageInventoryResponse)
def get_storage_record(
    record_id: int,
    db: Session = Depends(get_db),
):
    """Pobierz pojedynczy rekord zliczenia magazynowego."""
    record = storage_service.get_storage_record(db, record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rekord zliczenia nie znaleziony",
        )

    return StorageInventoryResponse(
        id=record.id,
        ingredient_id=record.ingredient_id,
        quantity_grams=record.quantity_grams,
        quantity_count=record.quantity_count,
        ingredient_name=record.ingredient.name if record.ingredient else None,
        ingredient_unit_type=record.ingredient.unit_type.value if record.ingredient else None,
        ingredient_unit_label=getattr(record.ingredient, 'unit_label', None) if record.ingredient else None,
        notes=record.notes,
        recorded_at=record.recorded_at,
        recorded_by=record.recorded_by,
    )


@router.post("/inventory/count", response_model=StorageInventoryResponse, status_code=status.HTTP_201_CREATED)
def create_storage_count(
    data: StorageInventoryCreate,
    db: Session = Depends(get_db),
):
    """Zapisz zliczenie magazynowe dla skladnika."""
    result = storage_service.create_storage_count(db, data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skladnik nie znaleziony",
        )

    return StorageInventoryResponse(
        id=result.id,
        ingredient_id=result.ingredient_id,
        quantity_grams=result.quantity_grams,
        quantity_count=result.quantity_count,
        ingredient_name=result.ingredient.name if result.ingredient else None,
        ingredient_unit_type=result.ingredient.unit_type.value if result.ingredient else None,
        ingredient_unit_label=getattr(result.ingredient, 'unit_label', None) if result.ingredient else None,
        notes=result.notes,
        recorded_at=result.recorded_at,
        recorded_by=result.recorded_by,
    )


@router.post("/inventory/count/bulk", response_model=StorageCountBulkResponse, status_code=status.HTTP_201_CREATED)
def create_storage_count_bulk(
    data: StorageCountBulkCreate,
    db: Session = Depends(get_db),
):
    """Zapisz zliczenie magazynowe dla wielu skladnikow naraz."""
    if not data.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lista skladnikow nie moze byc pusta",
        )

    results = storage_service.create_storage_count_bulk(
        db, data.items, notes=data.notes
    )

    if not results:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Zadne skladniki nie zostaly znalezione",
        )

    response_items = [
        StorageInventoryResponse(
            id=result.id,
            ingredient_id=result.ingredient_id,
            quantity_grams=result.quantity_grams,
            quantity_count=result.quantity_count,
            ingredient_name=result.ingredient.name if result.ingredient else None,
            ingredient_unit_type=result.ingredient.unit_type.value if result.ingredient else None,
            ingredient_unit_label=getattr(result.ingredient, 'unit_label', None) if result.ingredient else None,
            notes=result.notes,
            recorded_at=result.recorded_at,
            recorded_by=result.recorded_by,
        )
        for result in results
    ]

    return StorageCountBulkResponse(
        items=response_items,
        recorded_at=results[0].recorded_at if results else datetime.utcnow(),
    )


@router.get("/ingredient/{ingredient_id}/latest", response_model=StorageInventoryResponse)
def get_latest_count_for_ingredient(
    ingredient_id: int,
    db: Session = Depends(get_db),
):
    """Pobierz ostatnie zliczenie dla skladnika."""
    result = storage_service.get_latest_count_for_ingredient(db, ingredient_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brak zliczen dla tego skladnika",
        )

    return StorageInventoryResponse(
        id=result.id,
        ingredient_id=result.ingredient_id,
        quantity_grams=result.quantity_grams,
        quantity_count=result.quantity_count,
        ingredient_name=result.ingredient.name if result.ingredient else None,
        ingredient_unit_type=result.ingredient.unit_type.value if result.ingredient else None,
        ingredient_unit_label=getattr(result.ingredient, 'unit_label', None) if result.ingredient else None,
        notes=result.notes,
        recorded_at=result.recorded_at,
        recorded_by=result.recorded_by,
    )
