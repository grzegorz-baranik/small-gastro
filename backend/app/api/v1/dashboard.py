from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.api.deps import get_db
from app.schemas.dashboard import (
    DashboardOverview,
    IncomeBreakdown,
    ExpensesBreakdown,
    ProfitData,
    DiscrepancyWarning,
)
from app.services import dashboard_service

router = APIRouter()


@router.get("/overview", response_model=DashboardOverview)
def get_dashboard_overview(
    db: Session = Depends(get_db),
):
    """Pobierz przeglad pulpitu."""
    return dashboard_service.get_dashboard_overview(db)


@router.get("/income", response_model=IncomeBreakdown)
def get_income_breakdown(
    period: str = Query("today", regex="^(today|week|month)$"),
    db: Session = Depends(get_db),
):
    """Pobierz rozbicie przychodow."""
    return dashboard_service.get_income_breakdown(db, period)


@router.get("/expenses", response_model=ExpensesBreakdown)
def get_expenses_breakdown(
    period: str = Query("today", regex="^(today|week|month)$"),
    db: Session = Depends(get_db),
):
    """Pobierz rozbicie wydatkow."""
    return dashboard_service.get_expenses_breakdown(db, period)


@router.get("/profit", response_model=ProfitData)
def get_profit_data(
    period: str = Query("today", regex="^(today|week|month)$"),
    db: Session = Depends(get_db),
):
    """Pobierz dane o zysku."""
    return dashboard_service.get_profit_data(db, period)


@router.get("/warnings", response_model=list[DiscrepancyWarning])
def get_discrepancy_warnings(
    days_back: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
):
    """Pobierz ostrzezenia o rozbiezno sciach."""
    return dashboard_service.get_discrepancy_warnings(db, days_back)
