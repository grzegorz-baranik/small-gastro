"""
Daily Records API - Core daily operations endpoints.

Provides endpoints for:
- Opening and closing days
- Viewing day summaries
- Pre-filling from previous closing
- Editing closed days
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db
from app.services import daily_operations_service
from app.schemas.daily_operations import (
    OpenDayRequest,
    OpenDayResponse,
    CloseDayRequest,
    CloseDayResponse,
    DaySummaryResponse,
    PreviousClosingResponse,
    EditClosedDayRequest,
    EditClosedDayResponse,
    DailyRecordDetailResponse,
    PreviousDayStatusResponse,
)
from app.schemas.daily_record import DailyRecordResponse
from app.models.daily_record import DailyRecord, DayStatus


router = APIRouter()


# -----------------------------------------------------------------------------
# List Daily Records
# -----------------------------------------------------------------------------

@router.get("/", response_model=list[DailyRecordResponse])
def list_daily_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Pobierz liste rekordow dziennych.

    Zwraca rekordy posortowane od najnowszych.
    """
    items = db.query(DailyRecord).order_by(
        DailyRecord.date.desc()
    ).offset(skip).limit(limit).all()
    return items


# -----------------------------------------------------------------------------
# Get Today's Record
# -----------------------------------------------------------------------------

@router.get("/today", response_model=Optional[DailyRecordDetailResponse])
def get_today_record(
    db: Session = Depends(get_db),
):
    """
    Pobierz dzisiejszy rekord (lub null jesli nie istnieje).

    Zwraca pelne szczegoly dnia wlacznie ze snapshotami i wydarzeniami.
    """
    record = daily_operations_service.get_today_record(db)
    if not record:
        return None

    return daily_operations_service.get_daily_record_detail(db, record.id)


# -----------------------------------------------------------------------------
# Get Previous Closing (for pre-fill)
# -----------------------------------------------------------------------------

@router.get("/previous-closing", response_model=PreviousClosingResponse)
def get_previous_closing(
    db: Session = Depends(get_db),
):
    """
    Pobierz poprzedni stan zamkniecia do pre-fill otwarcia.

    Zwraca stany koncowe z ostatniego zamknietego dnia.
    Uzywane do wypelnienia formularza otwarcia dnia.
    """
    return daily_operations_service.get_previous_closing(db)


# -----------------------------------------------------------------------------
# Check Previous Day Status (VR-06)
# -----------------------------------------------------------------------------

@router.get("/check-previous", response_model=PreviousDayStatusResponse)
def check_previous_day_status(
    db: Session = Depends(get_db),
):
    """
    Sprawdz czy poprzedni dzien wymaga zamkniecia.

    VR-06: Ostrzezenie jesli poprzedni dzien nie jest zamkniety.

    Zwraca:
    - has_unclosed_previous: czy jest niezamkniety poprzedni dzien
    - unclosed_date: data niezamknietego dnia
    - unclosed_record_id: ID niezamknietego rekordu
    - message: komunikat w jezyku polskim
    """
    return daily_operations_service.check_previous_day_status(db)


# -----------------------------------------------------------------------------
# Open Day
# -----------------------------------------------------------------------------

@router.post("/open", response_model=OpenDayResponse, status_code=status.HTTP_201_CREATED)
def open_day(
    data: OpenDayRequest,
    force: bool = Query(False, description="Wymus otwarcie nawet jesli inny dzien jest otwarty"),
    db: Session = Depends(get_db),
):
    """
    Otworz nowy dzien z poczatkowymi stanami magazynowymi.

    - Tworzy nowy DailyRecord ze statusem 'open'
    - Tworzy InventorySnapshot dla kazdego skladnika (type='open', location='shop')
    - Ostrzega (ale pozwala) jesli poprzedni dzien nie jest zamkniety

    Query params:
    - force: Jesli true, pozwala otworzyc nawet gdy inny dzien jest otwarty

    Walidacja:
    - Nie mozna otworzyc dnia dla tej samej daty dwukrotnie
    - Domyslnie blokuje jesli inny dzien jest otwarty (chyba ze force=true)
    """
    response, error = daily_operations_service.open_day(db, data, force=force)

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    return response


# -----------------------------------------------------------------------------
# Close Day
# -----------------------------------------------------------------------------

@router.post("/{record_id}/close", response_model=CloseDayResponse)
def close_day(
    record_id: int,
    data: CloseDayRequest,
    db: Session = Depends(get_db),
):
    """
    Zamknij otwarty dzien ze stanami koncowymi.

    - Waliduje ze dzien istnieje i jest otwarty
    - Tworzy InventorySnapshot dla kazdego skladnika (type='close', location='shop')
    - Oblicza zuzycie dla kazdego skladnika: Otwarcie + Dostawy + Transfery - Straty - Zamkniecie
    - Aktualizuje status na 'closed' i ustawia closed_at

    Zwraca:
    - Obliczone zuzycie i podsumowanie
    """
    response, error = daily_operations_service.close_day(db, record_id, data)

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    return response


# -----------------------------------------------------------------------------
# Get Daily Record Detail
# -----------------------------------------------------------------------------

@router.get("/{record_id}", response_model=DailyRecordDetailResponse)
def get_daily_record(
    record_id: int,
    db: Session = Depends(get_db),
):
    """
    Pobierz rekord dzienny po ID z pelnymi szczegolami.

    Zawiera:
    - Snapshoty otwarcia i zamkniecia
    - Podsumowanie dostaw, transferow, strat
    """
    result = daily_operations_service.get_daily_record_detail(db, record_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rekord nie znaleziony"
        )

    return result


# -----------------------------------------------------------------------------
# Get Day Summary
# -----------------------------------------------------------------------------

@router.get("/{record_id}/summary", response_model=DaySummaryResponse)
def get_daily_summary(
    record_id: int,
    db: Session = Depends(get_db),
):
    """
    Pobierz pelne podsumowanie dnia.

    Zawiera:
    - Stany otwarcia i zamkniecia
    - Dostawy, transfery, straty
    - Obliczone zuzycie (jesli dzien zamkniety)
    """
    result = daily_operations_service.get_day_summary(db, record_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rekord nie znaleziony"
        )

    return result


# -----------------------------------------------------------------------------
# Edit Closed Day
# -----------------------------------------------------------------------------

@router.put("/{record_id}", response_model=EditClosedDayResponse)
def edit_closed_day(
    record_id: int,
    data: EditClosedDayRequest,
    db: Session = Depends(get_db),
):
    """
    Edytuj zamkniety dzien.

    Pozwala na:
    - Aktualizacje stanow koncowych
    - Przeliczenie zuzycia

    Uwaga: Mozna edytowac tylko zamkniete dni.
    """
    response, error = daily_operations_service.edit_closed_day(db, record_id, data)

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    return response


# -----------------------------------------------------------------------------
# Get Open Day
# -----------------------------------------------------------------------------

@router.get("/status/open", response_model=Optional[DailyRecordDetailResponse])
def get_open_day(
    db: Session = Depends(get_db),
):
    """
    Pobierz aktualnie otwarty dzien (jesli istnieje).

    Uzywane do sprawdzenia czy jakis dzien jest aktualnie otwarty.
    """
    record = daily_operations_service.get_open_day(db)
    if not record:
        return None

    return daily_operations_service.get_daily_record_detail(db, record.id)
