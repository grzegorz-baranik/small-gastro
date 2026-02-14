"""
Batches API Router

Endpoints for batch/expiry tracking:
- GET /batches/expiry-alerts - Get expiry warnings
- GET /batches/ingredient/{ingredient_id} - Get batches for ingredient (FIFO order)
- GET /batches/ingredient/{ingredient_id}/summary - Get batch summary
- GET /batches/{batch_id} - Get single batch details
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.services import batch_service
from app.schemas.batch import (
    BatchResponse,
    BatchListResponse,
    ExpiryAlertsListResponse,
    IngredientBatchSummary,
    EXPIRY_ALERT_DAYS,
)

router = APIRouter()


# -----------------------------------------------------------------------------
# Expiry Alerts (Static route - MUST come before path param routes)
# -----------------------------------------------------------------------------

@router.get(
    "/expiry-alerts",
    response_model=ExpiryAlertsListResponse,
    summary="Pobierz alerty o zbliżających się terminach ważności",
    description="""
    Zwraca listę partii ze zbliżającym się terminem ważności.

    Poziomy alertów:
    - **expired**: Już przeterminowane
    - **critical**: 0-2 dni do terminu
    - **warning**: 3-7 dni do terminu

    Można kontrolować zakres dni za pomocą parametru `days_ahead`.
    """
)
def get_expiry_alerts(
    days_ahead: int = Query(
        default=EXPIRY_ALERT_DAYS,
        ge=1,
        le=30,
        description="Liczba dni w przód do sprawdzenia (domyślnie 7)"
    ),
    db: Session = Depends(get_db)
) -> ExpiryAlertsListResponse:
    """Get expiry alerts for batches expiring within the specified days."""
    return batch_service.get_expiry_alerts(db, days_ahead=days_ahead)


# -----------------------------------------------------------------------------
# Ingredient Batches (Static path with parameter - before generic /{batch_id})
# -----------------------------------------------------------------------------

@router.get(
    "/ingredient/{ingredient_id}",
    response_model=BatchListResponse,
    summary="Pobierz partie dla składnika",
    description="""
    Zwraca wszystkie partie dla danego składnika, posortowane według FIFO
    (najstarsze pierwsze - do użycia jako pierwsze).

    Można filtrować po lokalizacji (storage/shop) i statusie aktywności.
    """
)
def get_batches_for_ingredient(
    ingredient_id: int,
    location: Optional[str] = Query(
        None,
        description="Filtruj po lokalizacji: 'storage' lub 'shop'"
    ),
    active_only: bool = Query(
        True,
        description="Czy zwracać tylko aktywne partie (z pozostałą ilością > 0)"
    ),
    db: Session = Depends(get_db)
) -> BatchListResponse:
    """Get all batches for an ingredient in FIFO order."""
    return batch_service.get_batches_for_ingredient(
        db,
        ingredient_id=ingredient_id,
        location=location,
        active_only=active_only
    )


@router.get(
    "/ingredient/{ingredient_id}/summary",
    response_model=IngredientBatchSummary,
    summary="Pobierz podsumowanie partii składnika",
    description="""
    Zwraca podsumowanie wszystkich partii dla składnika z:
    - Całkowitą ilością dostępną
    - Liczbą aktywnych partii
    - Liczbą partii ze zbliżającym się terminem
    - Listą partii w kolejności FIFO

    Przydatne do wyświetlania stanu magazynowego z informacją o partiach.
    """
)
def get_ingredient_batch_summary(
    ingredient_id: int,
    location: Optional[str] = Query(
        None,
        description="Filtruj po lokalizacji: 'storage' lub 'shop'"
    ),
    db: Session = Depends(get_db)
) -> IngredientBatchSummary:
    """Get batch summary for an ingredient."""
    summary, error = batch_service.get_ingredient_batch_summary(
        db,
        ingredient_id=ingredient_id,
        location=location
    )
    if error:
        raise HTTPException(status_code=404, detail=error)
    return summary


# -----------------------------------------------------------------------------
# Single Batch (Path parameter route - MUST come AFTER static routes)
# -----------------------------------------------------------------------------

@router.get(
    "/{batch_id}",
    response_model=BatchResponse,
    summary="Pobierz szczegóły partii",
    description="Zwraca pełne informacje o pojedynczej partii, włącznie z polami obliczeniowymi."
)
def get_batch(
    batch_id: int,
    db: Session = Depends(get_db)
) -> BatchResponse:
    """Get single batch by ID."""
    batch, error = batch_service.get_batch_by_id(db, batch_id)
    if error:
        raise HTTPException(status_code=404, detail=error)
    return batch
