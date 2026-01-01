from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from app.api.deps import get_db
from app.schemas.daily_record import (
    DailyRecordCreate,
    DailyRecordClose,
    DailyRecordResponse,
    DailyRecordSummary,
)
from app.services import daily_record_service

router = APIRouter()


@router.get("", response_model=list[DailyRecordResponse])
def list_daily_records(
    skip: int = 0,
    limit: int = 30,
    db: Session = Depends(get_db),
):
    """Pobierz liste rekordow dziennych."""
    items, _ = daily_record_service.get_daily_records(db, skip, limit)
    return items


@router.get("/today", response_model=DailyRecordResponse)
def get_today_record(
    db: Session = Depends(get_db),
):
    """Pobierz dzisiejszy rekord."""
    record = daily_record_service.get_today_record(db)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dzien nie zostal jeszcze otwarty",
        )
    return record


@router.post("/open", response_model=DailyRecordResponse, status_code=status.HTTP_201_CREATED)
def open_day(
    data: DailyRecordCreate,
    db: Session = Depends(get_db),
):
    """Otworz nowy dzien."""
    result = daily_record_service.open_day(db, data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dzien o tej dacie juz istnieje",
        )
    return result


@router.post("/{record_id}/close", response_model=DailyRecordResponse)
def close_day(
    record_id: int,
    data: DailyRecordClose,
    db: Session = Depends(get_db),
):
    """Zamknij dzien."""
    result = daily_record_service.close_day(db, record_id, data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nie mozna zamknac dnia. Rekord nie istnieje lub jest juz zamkniety.",
        )
    return result


@router.get("/{record_id}", response_model=DailyRecordResponse)
def get_daily_record(
    record_id: int,
    db: Session = Depends(get_db),
):
    """Pobierz rekord dzienny po ID."""
    record = daily_record_service.get_daily_record(db, record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rekord nie znaleziony",
        )
    return record


@router.get("/{record_id}/summary", response_model=DailyRecordSummary)
def get_daily_summary(
    record_id: int,
    db: Session = Depends(get_db),
):
    """Pobierz podsumowanie dnia z rozbiezno sciami."""
    summary = daily_record_service.get_daily_summary(db, record_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rekord nie znaleziony",
        )
    return summary
