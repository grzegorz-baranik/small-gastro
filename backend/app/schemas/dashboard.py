from pydantic import BaseModel
from typing import Optional
from datetime import date
from decimal import Decimal


class DashboardOverview(BaseModel):
    today_revenue: Decimal
    today_expenses: Decimal
    today_profit: Decimal
    week_revenue: Decimal
    week_expenses: Decimal
    week_profit: Decimal
    month_revenue: Decimal
    month_expenses: Decimal
    month_profit: Decimal
    day_is_open: bool
    active_warnings: int


class IncomeBreakdown(BaseModel):
    period: str  # today, week, month
    total: Decimal
    by_payment_method: dict[str, Decimal]
    by_day: Optional[dict[str, Decimal]] = None


class ExpensesBreakdown(BaseModel):
    period: str
    total: Decimal
    by_category: dict[str, Decimal]
    by_day: Optional[dict[str, Decimal]] = None


class ProfitData(BaseModel):
    period: str
    revenue: Decimal
    expenses: Decimal
    profit: Decimal
    margin_percent: Optional[Decimal] = None


class DiscrepancyWarning(BaseModel):
    id: int
    date: date
    ingredient_id: int
    ingredient_name: str
    expected_used: Decimal
    actual_used: Decimal
    discrepancy: Decimal
    discrepancy_percent: Decimal
    severity: str  # low, medium, high
