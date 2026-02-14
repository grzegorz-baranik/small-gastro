"""
Recorded Sales API - Manual sales entry endpoints.

Provides endpoints for:
- Recording sales during open day
- Listing recorded sales
- Getting day sales totals
- Voiding sales (soft delete)
- Reconciliation reports
- Product categories for sales UI
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db
from app.core.i18n import t
from app.schemas.recorded_sales import (
    RecordedSaleCreate,
    RecordedSaleResponse,
    RecordedSaleVoid,
    DaySalesTotal,
)
from app.schemas.reconciliation import ReconciliationReportResponse
from app.schemas.product_category import ProductCategoryResponse
from app.services import recorded_sales_service, reconciliation_service
from app.models.daily_record import DailyRecord, DayStatus
from app.models.product_category import ProductCategory


router = APIRouter()


# -----------------------------------------------------------------------------
# Record a Sale
# -----------------------------------------------------------------------------

@router.post(
    "/daily-records/{record_id}/sales",
    response_model=RecordedSaleResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_sale(
    record_id: int,
    data: RecordedSaleCreate,
    db: Session = Depends(get_db),
):
    """
    Zarejestruj nowa sprzedaz.

    Wymaga otwartego dnia. Sprzedaz jest zapisywana z aktualna cena wariantu
    produktu i moze byc pozniej anulowana (void) jesli potrzeba.

    Walidacja:
    - Dzien musi byc otwarty (status = 'open')
    - Wariant produktu musi istniec i byc aktywny
    """
    # Check if daily record exists and is open
    daily_record = db.query(DailyRecord).filter(DailyRecord.id == record_id).first()
    if not daily_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.daily_record_not_found"),
        )

    if daily_record.status != DayStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=t("errors.day_not_open_for_sales"),
        )

    # Record the sale
    result = recorded_sales_service.record_sale(db, record_id, data)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.variant_not_found"),
        )

    return result


# -----------------------------------------------------------------------------
# List Recorded Sales
# -----------------------------------------------------------------------------

@router.get(
    "/daily-records/{record_id}/sales",
    response_model=List[RecordedSaleResponse],
)
def list_recorded_sales(
    record_id: int,
    include_voided: bool = Query(False, description="Uwzglednij anulowane sprzedaze"),
    db: Session = Depends(get_db),
):
    """
    Pobierz liste zarejestrowanych sprzedazy dla dnia.

    Query params:
    - include_voided: Jesli true, zwraca rowniez anulowane sprzedaze

    Zwraca liste sprzedazy posortowana od najnowszych.
    """
    # Check if daily record exists
    daily_record = db.query(DailyRecord).filter(DailyRecord.id == record_id).first()
    if not daily_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.daily_record_not_found"),
        )

    return recorded_sales_service.list_sales(db, record_id, include_voided=include_voided)


# -----------------------------------------------------------------------------
# Get Day Sales Total
# -----------------------------------------------------------------------------

@router.get(
    "/daily-records/{record_id}/sales/total",
    response_model=DaySalesTotal,
)
def get_day_sales_total(
    record_id: int,
    db: Session = Depends(get_db),
):
    """
    Pobierz biezaca sume sprzedazy dla dnia.

    Zwraca:
    - total_pln: Laczna wartosc sprzedazy (bez anulowanych)
    - sales_count: Liczba transakcji sprzedazy
    - items_count: Laczna liczba sprzedanych sztuk
    """
    # Check if daily record exists
    daily_record = db.query(DailyRecord).filter(DailyRecord.id == record_id).first()
    if not daily_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.daily_record_not_found"),
        )

    return recorded_sales_service.get_day_total(db, record_id)


# -----------------------------------------------------------------------------
# Void a Sale
# -----------------------------------------------------------------------------

@router.post(
    "/daily-records/{record_id}/sales/{sale_id}/void",
    response_model=RecordedSaleResponse,
)
def void_sale(
    record_id: int,
    sale_id: int,
    data: RecordedSaleVoid,
    db: Session = Depends(get_db),
):
    """
    Anuluj zarejestrowana sprzedaz (soft delete).

    Sprzedaz nie jest usuwana, a oznaczana jako anulowana z powodem i notatkami.
    Anulowane sprzedaze nie sa wliczane do sum i raportow.

    Walidacja:
    - Dzien musi byc otwarty
    - Sprzedaz nie moze byc juz anulowana
    - Sprzedaz musi nalezec do tego dnia
    """
    # Check if daily record exists and is open
    daily_record = db.query(DailyRecord).filter(DailyRecord.id == record_id).first()
    if not daily_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.daily_record_not_found"),
        )

    if daily_record.status != DayStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=t("errors.cannot_void_sale_closed_day"),
        )

    # Void the sale
    result = recorded_sales_service.void_sale(db, record_id, sale_id, data)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=t("errors.sale_not_found_or_already_voided"),
        )

    return result


# -----------------------------------------------------------------------------
# Get Reconciliation Report
# -----------------------------------------------------------------------------

@router.get(
    "/daily-records/{record_id}/reconciliation",
    response_model=ReconciliationReportResponse,
)
def get_reconciliation_report(
    record_id: int,
    db: Session = Depends(get_db),
):
    """
    Pobierz raport uzgodnienia sprzedazy.

    Porownuje zarejestrowane sprzedaze z obliczonymi na podstawie zuzycia skladnikow.
    Pokazuje rozbieznosci i sugestie brakujacych sprzedazy.

    Zwraca:
    - recorded_total_pln: Suma zarejestrowanych sprzedazy
    - calculated_total_pln: Suma obliczonych sprzedazy
    - discrepancy_pln: Roznica w PLN
    - discrepancy_percent: Roznica w procentach
    - has_critical_discrepancy: Czy rozbieznosc przekracza prog krytyczny
    - has_no_recorded_sales: Czy brak zarejestrowanych sprzedazy
    - by_product: Szczegoly per produkt
    - suggestions: Sugestie brakujacych sprzedazy
    """
    # Check if daily record exists
    daily_record = db.query(DailyRecord).filter(DailyRecord.id == record_id).first()
    if not daily_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.daily_record_not_found"),
        )

    return reconciliation_service.get_reconciliation_report(db, record_id)


# -----------------------------------------------------------------------------
# List Product Categories
# -----------------------------------------------------------------------------

@router.get(
    "/products/categories",
    response_model=List[ProductCategoryResponse],
)
def list_product_categories(
    db: Session = Depends(get_db),
):
    """
    Pobierz liste kategorii produktow.

    Kategorie sluza do grupowania produktow w interfejsie sprzedazy
    (np. "Kebaby", "Burgery", "Napoje", "Dodatki").

    Zwraca liste posortowana po sort_order.
    """
    categories = (
        db.query(ProductCategory)
        .order_by(ProductCategory.sort_order, ProductCategory.name)
        .all()
    )
    return categories
