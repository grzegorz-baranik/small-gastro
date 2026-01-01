"""
Mid-Day Operations API - Endpoints for mid-day events.

Provides endpoints for:
- Deliveries: Record ingredient deliveries with cost
- Storage Transfers: Move ingredients from storage to shop
- Spoilage: Record wasted/damaged ingredients

All operations are tied to an open daily record.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db
from app.services import mid_day_operations_service
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
)


router = APIRouter()


# -----------------------------------------------------------------------------
# Deliveries
# -----------------------------------------------------------------------------

@router.post("/deliveries", response_model=DeliveryResponse, status_code=status.HTTP_201_CREATED)
def create_delivery(
    data: DeliveryCreate,
    db: Session = Depends(get_db),
):
    """
    Zarejestruj dostawe skladnika.

    Tworzy rekord dostawy dla otwartego dnia.
    Dostawy zwiekszaja dostepna ilosc skladnika.

    Wymagane:
    - daily_record_id: ID otwartego dnia
    - ingredient_id: ID skladnika
    - quantity: Ilosc (w jednostce skladnika)
    - price_pln: Cena dostawy

    Walidacja:
    - Dzien musi byc otwarty
    - Skladnik musi istniec i byc aktywny
    - Ilosc musi byc > 0
    - Cena musi byc >= 0
    """
    response, error = mid_day_operations_service.create_delivery(db, data)

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    return response


@router.get("/deliveries", response_model=DeliveryListResponse)
def list_deliveries(
    daily_record_id: Optional[int] = Query(None, description="Filtruj po ID dnia"),
    db: Session = Depends(get_db),
):
    """
    Pobierz liste dostaw.

    Opcjonalnie filtruj po daily_record_id.
    Wyniki posortowane od najnowszych.
    """
    return mid_day_operations_service.get_deliveries(db, daily_record_id)


@router.get("/deliveries/{delivery_id}", response_model=DeliveryResponse)
def get_delivery(
    delivery_id: int,
    db: Session = Depends(get_db),
):
    """
    Pobierz dostawe po ID.
    """
    response, error = mid_day_operations_service.get_delivery_by_id(db, delivery_id)

    if error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error
        )

    return response


@router.delete("/deliveries/{delivery_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_delivery(
    delivery_id: int,
    db: Session = Depends(get_db),
):
    """
    Usun dostawe.

    Mozna usuwac tylko dostawy z otwartego dnia.
    """
    success, error = mid_day_operations_service.delete_delivery(db, delivery_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    return None


# -----------------------------------------------------------------------------
# Storage Transfers
# -----------------------------------------------------------------------------

@router.post("/transfers", response_model=StorageTransferResponse, status_code=status.HTTP_201_CREATED)
def create_storage_transfer(
    data: StorageTransferCreate,
    db: Session = Depends(get_db),
):
    """
    Zarejestruj transfer z magazynu.

    Tworzy rekord transferu skladnika z magazynu do sklepu.
    Transfery zwiekszaja dostepna ilosc w sklepie.

    Wymagane:
    - daily_record_id: ID otwartego dnia
    - ingredient_id: ID skladnika
    - quantity: Ilosc do przeniesienia

    Walidacja:
    - Dzien musi byc otwarty
    - Skladnik musi istniec i byc aktywny
    - Ilosc musi byc > 0
    """
    response, error = mid_day_operations_service.create_storage_transfer(db, data)

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    return response


@router.get("/transfers", response_model=StorageTransferListResponse)
def list_storage_transfers(
    daily_record_id: Optional[int] = Query(None, description="Filtruj po ID dnia"),
    db: Session = Depends(get_db),
):
    """
    Pobierz liste transferow z magazynu.

    Opcjonalnie filtruj po daily_record_id.
    Wyniki posortowane od najnowszych.
    """
    return mid_day_operations_service.get_storage_transfers(db, daily_record_id)


@router.get("/transfers/{transfer_id}", response_model=StorageTransferResponse)
def get_storage_transfer(
    transfer_id: int,
    db: Session = Depends(get_db),
):
    """
    Pobierz transfer po ID.
    """
    response, error = mid_day_operations_service.get_storage_transfer_by_id(db, transfer_id)

    if error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error
        )

    return response


@router.delete("/transfers/{transfer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_storage_transfer(
    transfer_id: int,
    db: Session = Depends(get_db),
):
    """
    Usun transfer.

    Mozna usuwac tylko transfery z otwartego dnia.
    """
    success, error = mid_day_operations_service.delete_storage_transfer(db, transfer_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    return None


# -----------------------------------------------------------------------------
# Spoilage
# -----------------------------------------------------------------------------

@router.post("/spoilage", response_model=SpoilageResponse, status_code=status.HTTP_201_CREATED)
def create_spoilage(
    data: SpoilageCreate,
    db: Session = Depends(get_db),
):
    """
    Zarejestruj strate skladnika.

    Tworzy rekord straty (przeterminowanie, uszkodzenie itp.).
    Straty zmniejszaja dostepna ilosc skladnika.

    Wymagane:
    - daily_record_id: ID otwartego dnia
    - ingredient_id: ID skladnika
    - quantity: Ilosc stracona
    - reason: Przyczyna (expired, over_prepared, contaminated, equipment_failure, other)

    Opcjonalne:
    - notes: Dodatkowe uwagi

    Walidacja:
    - Dzien musi byc otwarty
    - Skladnik musi istniec i byc aktywny
    - Ilosc musi byc > 0
    """
    response, error = mid_day_operations_service.create_spoilage(db, data)

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    return response


@router.get("/spoilage", response_model=SpoilageListResponse)
def list_spoilages(
    daily_record_id: Optional[int] = Query(None, description="Filtruj po ID dnia"),
    db: Session = Depends(get_db),
):
    """
    Pobierz liste strat.

    Opcjonalnie filtruj po daily_record_id.
    Wyniki posortowane od najnowszych.
    """
    return mid_day_operations_service.get_spoilages(db, daily_record_id)


@router.get("/spoilage/{spoilage_id}", response_model=SpoilageResponse)
def get_spoilage(
    spoilage_id: int,
    db: Session = Depends(get_db),
):
    """
    Pobierz strate po ID.
    """
    response, error = mid_day_operations_service.get_spoilage_by_id(db, spoilage_id)

    if error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error
        )

    return response


@router.delete("/spoilage/{spoilage_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_spoilage(
    spoilage_id: int,
    db: Session = Depends(get_db),
):
    """
    Usun strate.

    Mozna usuwac tylko straty z otwartego dnia.
    """
    success, error = mid_day_operations_service.delete_spoilage(db, spoilage_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    return None
