from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.sales import (
    SalesItemCreate,
    SalesItemResponse,
    DailySalesSummary,
)
from app.services import sales_service, daily_record_service

router = APIRouter()


@router.get("/today", response_model=DailySalesSummary)
def get_today_sales(
    db: Session = Depends(get_db),
):
    """Pobierz dzisiejsza sprzedaz."""
    summary = sales_service.get_today_sales(db)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dzien nie zostal jeszcze otwarty",
        )
    return summary


@router.get("/daily-record/{daily_record_id}", response_model=DailySalesSummary)
def get_sales_for_day(
    daily_record_id: int,
    db: Session = Depends(get_db),
):
    """Pobierz sprzedaz dla danego dnia."""
    summary = sales_service.get_daily_sales_summary(db, daily_record_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rekord nie znaleziony",
        )
    return summary


@router.post("/", response_model=SalesItemResponse, status_code=status.HTTP_201_CREATED)
def create_sale(
    data: SalesItemCreate,
    db: Session = Depends(get_db),
):
    """Zarejestruj sprzedaz (wymaga otwartego dnia)."""
    # Get today's record
    today_record = daily_record_service.get_today_record(db)
    if not today_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dzien nie jest otwarty. Otworz dzien przed rejestrowaniem sprzedazy.",
        )

    sale = sales_service.create_sale(db, today_record.id, data)
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nie mozna utworzyc sprzedazy. Sprawdz czy produkt istnieje i czy dzien jest otwarty.",
        )

    return SalesItemResponse(
        id=sale.id,
        daily_record_id=sale.daily_record_id,
        product_id=sale.product_id,
        product_name=sale.product.name if sale.product else None,
        quantity_sold=sale.quantity_sold,
        unit_price=sale.unit_price,
        total_price=sale.total_price,
        created_at=sale.created_at,
    )


@router.delete("/{sale_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sale(
    sale_id: int,
    db: Session = Depends(get_db),
):
    """Usun sprzedaz (tylko gdy dzien jest otwarty)."""
    result = sales_service.delete_sale(db, sale_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nie mozna usunac sprzedazy. Rekord nie istnieje lub dzien jest zamkniety.",
        )
