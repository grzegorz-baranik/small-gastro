from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.api.deps import get_db
from app.core.i18n import t
from app.schemas.wage_analytics import WageAnalyticsResponse
from app.services import wage_analytics_service

router = APIRouter()


@router.get("", response_model=WageAnalyticsResponse)
def get_wage_analytics(
    month: int = Query(..., ge=1, le=12, description="Miesiac (1-12)"),
    year: int = Query(..., ge=2000, le=2100, description="Rok"),
    employee_id: Optional[int] = Query(None, description="Filtruj po pracowniku"),
    db: Session = Depends(get_db),
):
    """
    Pobierz analityke wynagrodzen za okres.

    Zwraca podsumowanie wynagrodzen oraz rozklad per pracownik.
    Porownuje z poprzednim miesiacem.
    """
    analytics = wage_analytics_service.get_wage_analytics(
        db=db,
        month=month,
        year=year,
        employee_id=employee_id,
    )
    return analytics
