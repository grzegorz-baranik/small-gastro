"""
Daily Records API - Core daily operations endpoints.

Provides endpoints for:
- Opening and closing days
- Viewing day summaries
- Pre-filling from previous closing
- Editing closed days
- Day closing wizard operations
"""

from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db
from app.core.i18n import t
from app.services import daily_operations_service
from app.services.day_wizard_service import (
    DayWizardService,
    DailyRecordNotFoundError,
    DayNotOpenError,
    InventoryNotEnteredError,
)
from app.schemas.daily_operations import (
    OpenDayRequest,
    OpenDayResponse,
    CloseDayRequest,
    CloseDayResponse,
    DaySummaryResponse,
    DayEventsSummary,
    PreviousClosingResponse,
    EditClosedDayRequest,
    EditClosedDayResponse,
    DailyRecordDetailResponse,
    PreviousDayStatusResponse,
    UpdateOpeningInventoryRequest,
    UpdateOpeningInventoryResponse,
)
from app.schemas.daily_record import DailyRecordResponse
from app.schemas.day_wizard import (
    WizardStateResponse,
    CompleteOpeningRequest,
    CompleteOpeningResponse,
    SuggestedShiftsResponse,
    SalesPreviewResponse,
)
from app.models.daily_record import DailyRecord, DayStatus
from app.models.inventory_snapshot import InventorySnapshot
from app.models.delivery import Delivery
from app.models.storage_transfer import StorageTransfer
from app.models.spoilage import Spoilage
from app.models.transaction import Transaction
from app.models.calculated_sale import CalculatedSale


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
# Get Recent Days (MUST be before /{record_id} routes to avoid path conflicts)
# -----------------------------------------------------------------------------

@router.get("/recent")
def get_recent_days(
    limit: int = Query(7, ge=1, le=30, description="Liczba dni do zwrocenia"),
    db: Session = Depends(get_db),
):
    """
    Pobierz ostatnie rekordy dzienne (do wyswietlenia historii).

    Zwraca uproszczone rekordy z liczba alertow.
    """
    return daily_operations_service.get_recent_records(db, limit)


# -----------------------------------------------------------------------------
# Get Open Day (MUST be before /{record_id} routes to avoid path conflicts)
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


# =============================================================================
# WIZARD ENDPOINTS (for Day Closing Wizard feature)
# These must come BEFORE /{record_id} routes to avoid path conflicts
# =============================================================================


@router.get("/{record_id}/wizard-state", response_model=WizardStateResponse)
def get_wizard_state(
    record_id: int,
    db: Session = Depends(get_db),
):
    """
    Pobierz aktualny stan kreatora zamykania dnia.

    Zwraca:
    - current_step: aktualny krok ('opening', 'mid_day', 'closing', 'completed')
    - opening: stan kroku otwarcia
    - mid_day: stan kroku operacji w ciagu dnia
    - closing: stan kroku zamkniecia
    """
    service = DayWizardService(db)

    try:
        return service.get_wizard_state(record_id)
    except DailyRecordNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.record_not_found")
        )


@router.post("/{record_id}/complete-opening", response_model=CompleteOpeningResponse)
def complete_opening(
    record_id: int,
    data: CompleteOpeningRequest,
    db: Session = Depends(get_db),
):
    """
    Zakoncz krok otwarcia dnia.

    Wymaga:
    - confirmed_shifts: lista zatwierdzonych zmian pracownikow
    - opening_inventory: lista stanow poczatkowych skladnikow

    Walidacja:
    - Wymagana co najmniej jedna zmiana pracownika
    - Wymagany co najmniej jeden stan magazynowy
    """
    service = DayWizardService(db)

    try:
        return service.complete_opening(record_id, data)
    except DailyRecordNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.record_not_found")
        )
    except DayNotOpenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=t("errors.day_not_open")
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except InventoryNotEnteredError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{record_id}/suggested-shifts", response_model=SuggestedShiftsResponse)
def get_suggested_shifts(
    record_id: int,
    db: Session = Depends(get_db),
):
    """
    Pobierz sugerowane zmiany na podstawie szablonow.

    Zwraca liste sugerowanych zmian na podstawie:
    - Szablonow zmian (jesli istnieja)
    - Nadpisanych zmian dla danego dnia
    """
    service = DayWizardService(db)

    try:
        record = db.query(DailyRecord).filter(DailyRecord.id == record_id).first()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t("errors.record_not_found")
            )

        shifts = service.get_suggested_shifts(record_id, record.date)
        return SuggestedShiftsResponse(suggested_shifts=shifts)
    except DailyRecordNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.record_not_found")
        )


@router.get("/{record_id}/sales-preview")
def get_sales_preview(
    record_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Pobierz podglad sprzedazy na podstawie stanow zamkniecia.

    Query params:
    - closing_inventory[ingredient_id]: ilosc zamkniecia dla skladnika

    Przyklad:
    GET /daily-records/1/sales-preview?closing_inventory[1]=38.0&closing_inventory[2]=80

    Zwraca:
    - ingredients_used: lista zuzycia skladnikow
    - calculated_sales: lista wyliczonej sprzedazy
    - summary: podsumowanie finansowe
    - warnings: ostrzezenia (np. rozbieznosci)
    """
    import re

    # Parse closing_inventory from query params
    # Format: closing_inventory[1]=38.0 becomes {1: Decimal("38.0")}
    closing_inventory: dict[int, Decimal] = {}

    for key, value in request.query_params.items():
        # Match closing_inventory[id] pattern
        match = re.match(r'closing_inventory\[(\d+)\]', key)
        if match:
            ingredient_id = int(match.group(1))
            try:
                closing_inventory[ingredient_id] = Decimal(str(value))
            except (ValueError, TypeError):
                pass  # Skip invalid values

    service = DayWizardService(db)

    try:
        result = service.calculate_sales_preview(record_id, closing_inventory)
        return result
    except DailyRecordNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.record_not_found")
        )


# =============================================================================
# END WIZARD ENDPOINTS
# =============================================================================


# -----------------------------------------------------------------------------
# Update Opening Inventory
# -----------------------------------------------------------------------------

@router.put("/{record_id}/opening-inventory", response_model=UpdateOpeningInventoryResponse)
def update_opening_inventory(
    record_id: int,
    data: UpdateOpeningInventoryRequest,
    db: Session = Depends(get_db),
):
    """
    Aktualizuj stany poczatkowe dla otwartego dnia.

    Pozwala na korekte stanow poczatkowych dopoki dzien jest otwarty.
    Przydatne gdy zauwazono blad po otwarciu dnia.

    Walidacja:
    - Mozna aktualizowac tylko dni ze statusem 'open'
    - Zastepuje wszystkie istniejace stany poczatkowe nowymi wartosciami

    Zwraca:
    - Zaktualizowany rekord dnia z nowymi stanami poczatkowymi
    """
    response, error = daily_operations_service.update_opening_inventory(
        db, record_id, data.items
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    return response


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
            detail=t("errors.record_not_found")
        )

    return result


# -----------------------------------------------------------------------------
# Get Day Events
# -----------------------------------------------------------------------------

@router.get("/{record_id}/events", response_model=DayEventsSummary)
def get_day_events(
    record_id: int,
    db: Session = Depends(get_db),
):
    """
    Pobierz podsumowanie wydarzen dnia (dostawy, transfery, straty).

    Zwraca uproszczone podsumowanie wydarzen.
    """
    result = daily_operations_service.get_day_events(db, record_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.record_not_found")
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
            detail=t("errors.record_not_found")
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
# Delete Daily Record (for testing)
# -----------------------------------------------------------------------------

@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_daily_record(
    record_id: int,
    db: Session = Depends(get_db),
):
    """
    Usun rekord dzienny (tylko do testow).

    UWAGA: Ta operacja usuwa rowniez wszystkie powiazane dane:
    - Snapshoty inwentarza
    - Dostawy
    - Transfery
    - Straty
    - Transakcje
    """
    record = db.query(DailyRecord).filter(DailyRecord.id == record_id).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.record_not_found")
        )

    # Delete all related records (cascading should handle most, but be explicit)
    db.query(InventorySnapshot).filter(InventorySnapshot.daily_record_id == record_id).delete()
    db.query(Delivery).filter(Delivery.daily_record_id == record_id).delete()
    db.query(StorageTransfer).filter(StorageTransfer.daily_record_id == record_id).delete()
    db.query(Spoilage).filter(Spoilage.daily_record_id == record_id).delete()
    db.query(Transaction).filter(Transaction.daily_record_id == record_id).delete()
    db.query(CalculatedSale).filter(CalculatedSale.daily_record_id == record_id).delete()

    db.delete(record)
    db.commit()
