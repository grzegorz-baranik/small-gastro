"""
Pydantic schemas for reporting endpoints.

Reports include:
- Daily summary report (podsumowanie dnia)
- Monthly trends report (trendy miesieczne)
- Ingredient usage report (zuzycie skladnikow)
- Spoilage report (straty)
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date, datetime
from decimal import Decimal


# -----------------------------------------------------------------------------
# Common Request Schemas
# -----------------------------------------------------------------------------

class DateRangeRequest(BaseModel):
    """Request schema for date range filtering."""
    start_date: date = Field(..., description="Data poczatkowa zakresu")
    end_date: date = Field(..., description="Data koncowa zakresu")

    @field_validator("end_date")
    @classmethod
    def end_date_not_before_start(cls, v, info):
        start = info.data.get("start_date")
        if start and v < start:
            raise ValueError("Data koncowa nie moze byc wczesniejsza niz data poczatkowa")
        return v


class IngredientUsageRequest(DateRangeRequest):
    """Request for ingredient usage report with optional ingredient filter."""
    ingredient_ids: Optional[list[int]] = Field(
        default=None,
        description="Lista ID skladnikow do filtrowania (puste = wszystkie)"
    )


class SpoilageReportRequest(DateRangeRequest):
    """Request for spoilage report with grouping option."""
    group_by: str = Field(
        default="date",
        description="Grupowanie: 'ingredient', 'reason', lub 'date'"
    )

    @field_validator("group_by")
    @classmethod
    def validate_group_by(cls, v):
        allowed = {"ingredient", "reason", "date"}
        if v not in allowed:
            raise ValueError(f"Nieprawidlowe grupowanie. Dozwolone: {', '.join(allowed)}")
        return v


# -----------------------------------------------------------------------------
# Daily Summary Report Schemas
# -----------------------------------------------------------------------------

class DailySummaryInventoryItem(BaseModel):
    """Single inventory item in daily summary report."""
    ingredient_id: int
    ingredient_name: str
    unit_label: str
    opening: Decimal
    deliveries: Decimal
    transfers: Decimal
    spoilage: Decimal
    closing: Decimal
    usage: Decimal
    discrepancy: Optional[Decimal] = None
    discrepancy_percent: Optional[Decimal] = None
    discrepancy_level: Optional[str] = None


class DailySummaryProductItem(BaseModel):
    """Single product sold item in daily summary report."""
    product_id: int
    product_name: str
    variant_id: Optional[int]
    variant_name: Optional[str]
    quantity_sold: Decimal
    unit_price_pln: Decimal
    revenue_pln: Decimal


class DailySummaryDiscrepancyAlert(BaseModel):
    """Discrepancy alert in daily summary report."""
    ingredient_id: int
    ingredient_name: str
    discrepancy_percent: Decimal
    level: str  # 'ok', 'warning', 'critical'
    message: str


class DailySummaryFinancials(BaseModel):
    """Financial summary in daily summary report."""
    total_income_pln: Decimal
    total_delivery_cost_pln: Decimal
    total_spoilage_cost_pln: Decimal
    net_profit_pln: Decimal


class DailySummaryReportResponse(BaseModel):
    """Full daily summary report response."""
    record_id: int
    date: date
    day_of_week: str  # Polish day name
    opening_time: Optional[str]
    closing_time: Optional[str]
    status: str

    # Inventory table
    inventory_items: list[DailySummaryInventoryItem] = []

    # Products sold table
    products_sold: list[DailySummaryProductItem] = []

    # Financial summary
    financials: DailySummaryFinancials

    # Discrepancy alerts
    discrepancy_alerts: list[DailySummaryDiscrepancyAlert] = []

    notes: Optional[str] = None


# -----------------------------------------------------------------------------
# Monthly Trends Report Schemas
# -----------------------------------------------------------------------------

class MonthlyTrendItem(BaseModel):
    """Single day's trend data in monthly trends report."""
    date: date
    day_of_week: str
    income_pln: Decimal
    delivery_cost_pln: Decimal
    spoilage_cost_pln: Decimal
    profit_pln: Decimal


class MonthlyBestWorstDay(BaseModel):
    """Best or worst day information."""
    date: date
    day_of_week: str
    profit_pln: Decimal


class MonthlyTrendsReportResponse(BaseModel):
    """Full monthly trends report response."""
    start_date: date
    end_date: date
    items: list[MonthlyTrendItem] = []

    # Summary statistics
    total_income_pln: Decimal
    total_delivery_cost_pln: Decimal
    total_spoilage_cost_pln: Decimal
    total_profit_pln: Decimal
    avg_daily_income_pln: Decimal
    avg_daily_profit_pln: Decimal

    # Best/worst days
    best_day: Optional[MonthlyBestWorstDay] = None
    worst_day: Optional[MonthlyBestWorstDay] = None

    days_count: int


# -----------------------------------------------------------------------------
# Ingredient Usage Report Schemas
# -----------------------------------------------------------------------------

class IngredientUsageReportItem(BaseModel):
    """Single usage record in ingredient usage report."""
    date: date
    day_of_week: str
    ingredient_id: int
    ingredient_name: str
    unit_label: str
    opening: Decimal
    deliveries: Decimal
    transfers: Decimal
    spoilage: Decimal
    closing: Decimal
    usage: Decimal
    discrepancy: Optional[Decimal] = None
    discrepancy_percent: Optional[Decimal] = None


class IngredientUsageSummaryItem(BaseModel):
    """Summary for a single ingredient in usage report."""
    ingredient_id: int
    ingredient_name: str
    unit_label: str
    total_used: Decimal
    avg_daily_usage: Decimal
    days_with_data: int


class IngredientUsageReportResponse(BaseModel):
    """Full ingredient usage report response."""
    start_date: date
    end_date: date
    filtered_ingredient_ids: Optional[list[int]] = None
    items: list[IngredientUsageReportItem] = []
    summary: list[IngredientUsageSummaryItem] = []


# -----------------------------------------------------------------------------
# Spoilage Report Schemas
# -----------------------------------------------------------------------------

class SpoilageReportItem(BaseModel):
    """Single spoilage record in spoilage report."""
    id: int
    date: date
    day_of_week: str
    ingredient_id: int
    ingredient_name: str
    unit_label: str
    quantity: Decimal
    reason: str
    reason_label: str  # Polish label for the reason
    notes: Optional[str]


class SpoilageByReasonSummary(BaseModel):
    """Summary of spoilage grouped by reason."""
    reason: str
    reason_label: str
    total_count: int
    total_quantity: Decimal  # Note: mixed units if different ingredients


class SpoilageByIngredientSummary(BaseModel):
    """Summary of spoilage grouped by ingredient."""
    ingredient_id: int
    ingredient_name: str
    unit_label: str
    total_count: int
    total_quantity: Decimal


class SpoilageReportResponse(BaseModel):
    """Full spoilage report response."""
    start_date: date
    end_date: date
    group_by: str
    items: list[SpoilageReportItem] = []
    by_reason: list[SpoilageByReasonSummary] = []
    by_ingredient: list[SpoilageByIngredientSummary] = []
    total_count: int
