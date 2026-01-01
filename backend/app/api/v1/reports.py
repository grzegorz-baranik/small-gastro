"""
Reports API Endpoints

Provides endpoints for generating and exporting reports:
- Daily summary report (podsumowanie dnia)
- Monthly trends report (trendy miesieczne)
- Ingredient usage report (zuzycie skladnikow)
- Spoilage report (straty)

Each report has both a JSON endpoint and an Excel export endpoint.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.reports import (
    DateRangeRequest,
    IngredientUsageRequest,
    SpoilageReportRequest,
    DailySummaryReportResponse,
    MonthlyTrendsReportResponse,
    IngredientUsageReportResponse,
    SpoilageReportResponse,
)
from app.services import reports_service

router = APIRouter()

# Excel content type
EXCEL_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


# -----------------------------------------------------------------------------
# Daily Summary Report
# -----------------------------------------------------------------------------

@router.get(
    "/daily/{record_id}",
    response_model=DailySummaryReportResponse,
    summary="Podsumowanie dnia",
    description="Generuje pelny raport podsumowania dnia dla podanego rekordu dziennego.",
)
def get_daily_summary_report(
    record_id: int,
    db: Session = Depends(get_db),
):
    """
    Get daily summary report for a specific daily record.

    Returns full day summary including:
    - Inventory table with opening, deliveries, transfers, spoilage, closing, usage
    - Products sold with quantities and revenue
    - Financial summary (income, costs, profit)
    - Discrepancy alerts
    """
    report = reports_service.get_daily_summary_report(db, record_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rekord dzienny nie znaleziony"
        )
    return report


@router.get(
    "/daily/{record_id}/export",
    summary="Eksport podsumowania dnia do Excel",
    description="Eksportuje raport podsumowania dnia do pliku Excel.",
)
def export_daily_summary_report(
    record_id: int,
    db: Session = Depends(get_db),
):
    """
    Export daily summary report to Excel file.

    Returns an Excel file (.xlsx) with the daily summary report.
    """
    report = reports_service.get_daily_summary_report(db, record_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rekord dzienny nie znaleziony"
        )

    excel_file = reports_service.export_daily_summary_to_excel(report)
    filename = f"podsumowanie_dnia_{report.date}.xlsx"

    return StreamingResponse(
        excel_file,
        media_type=EXCEL_CONTENT_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# -----------------------------------------------------------------------------
# Monthly Trends Report
# -----------------------------------------------------------------------------

@router.post(
    "/monthly-trends",
    response_model=MonthlyTrendsReportResponse,
    summary="Trendy miesieczne",
    description="Generuje raport trendow miesiecznych dla podanego zakresu dat.",
)
def get_monthly_trends_report(
    request: DateRangeRequest,
    db: Session = Depends(get_db),
):
    """
    Get monthly trends report for a date range.

    Returns aggregated data including:
    - Daily income, delivery costs, spoilage costs, profit
    - Total and average statistics
    - Best and worst performing days
    """
    report = reports_service.get_monthly_trends_report(
        db,
        request.start_date,
        request.end_date
    )
    return report


@router.post(
    "/monthly-trends/export",
    summary="Eksport trendow miesiecznych do Excel",
    description="Eksportuje raport trendow miesiecznych do pliku Excel.",
)
def export_monthly_trends_report(
    request: DateRangeRequest,
    db: Session = Depends(get_db),
):
    """
    Export monthly trends report to Excel file.

    Returns an Excel file (.xlsx) with the monthly trends report.
    """
    report = reports_service.get_monthly_trends_report(
        db,
        request.start_date,
        request.end_date
    )

    excel_file = reports_service.export_monthly_trends_to_excel(report)
    filename = f"trendy_{request.start_date}_do_{request.end_date}.xlsx"

    return StreamingResponse(
        excel_file,
        media_type=EXCEL_CONTENT_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# -----------------------------------------------------------------------------
# Ingredient Usage Report
# -----------------------------------------------------------------------------

@router.post(
    "/ingredient-usage",
    response_model=IngredientUsageReportResponse,
    summary="Zuzycie skladnikow",
    description="Generuje raport zuzycia skladnikow dla podanego zakresu dat.",
)
def get_ingredient_usage_report(
    request: IngredientUsageRequest,
    db: Session = Depends(get_db),
):
    """
    Get ingredient usage report for a date range.

    Optionally filter by specific ingredient IDs.

    Returns:
    - Daily usage data for each ingredient
    - Summary with total and average usage per ingredient
    """
    report = reports_service.get_ingredient_usage_report(
        db,
        request.start_date,
        request.end_date,
        request.ingredient_ids
    )
    return report


@router.post(
    "/ingredient-usage/export",
    summary="Eksport zuzycia skladnikow do Excel",
    description="Eksportuje raport zuzycia skladnikow do pliku Excel.",
)
def export_ingredient_usage_report(
    request: IngredientUsageRequest,
    db: Session = Depends(get_db),
):
    """
    Export ingredient usage report to Excel file.

    Returns an Excel file (.xlsx) with the ingredient usage report.
    """
    report = reports_service.get_ingredient_usage_report(
        db,
        request.start_date,
        request.end_date,
        request.ingredient_ids
    )

    excel_file = reports_service.export_ingredient_usage_to_excel(report)
    filename = f"zuzycie_skladnikow_{request.start_date}_do_{request.end_date}.xlsx"

    return StreamingResponse(
        excel_file,
        media_type=EXCEL_CONTENT_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# -----------------------------------------------------------------------------
# Spoilage Report
# -----------------------------------------------------------------------------

@router.post(
    "/spoilage",
    response_model=SpoilageReportResponse,
    summary="Raport strat",
    description="Generuje raport strat dla podanego zakresu dat.",
)
def get_spoilage_report(
    request: SpoilageReportRequest,
    db: Session = Depends(get_db),
):
    """
    Get spoilage report for a date range.

    group_by options:
    - 'date': Sort by date (default)
    - 'ingredient': Group by ingredient
    - 'reason': Group by spoilage reason

    Returns:
    - Individual spoilage records
    - Summary by reason (count and quantity)
    - Summary by ingredient (count and quantity)
    """
    report = reports_service.get_spoilage_report(
        db,
        request.start_date,
        request.end_date,
        request.group_by
    )
    return report


@router.post(
    "/spoilage/export",
    summary="Eksport raportu strat do Excel",
    description="Eksportuje raport strat do pliku Excel.",
)
def export_spoilage_report(
    request: SpoilageReportRequest,
    db: Session = Depends(get_db),
):
    """
    Export spoilage report to Excel file.

    Returns an Excel file (.xlsx) with the spoilage report.
    """
    report = reports_service.get_spoilage_report(
        db,
        request.start_date,
        request.end_date,
        request.group_by
    )

    excel_file = reports_service.export_spoilage_to_excel(report)
    filename = f"straty_{request.start_date}_do_{request.end_date}.xlsx"

    return StreamingResponse(
        excel_file,
        media_type=EXCEL_CONTENT_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
