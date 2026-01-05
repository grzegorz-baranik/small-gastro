from pydantic import BaseModel
from decimal import Decimal


class WageSummary(BaseModel):
    """Summary of wage statistics for a period."""
    total_wages: Decimal
    total_hours: float
    avg_cost_per_hour: Decimal


class EmployeeWageStats(BaseModel):
    """Wage statistics for a single employee."""
    employee_id: int
    employee_name: str
    position_name: str
    hours_worked: float
    wages_paid: Decimal
    cost_per_hour: Decimal
    previous_month_wages: Decimal | None
    change_percent: float | None


class WageAnalyticsResponse(BaseModel):
    """Complete wage analytics response with summary and per-employee breakdown."""
    summary: WageSummary
    previous_month_summary: WageSummary | None
    by_employee: list[EmployeeWageStats]


class HoursCalculationResponse(BaseModel):
    """Response for hours calculation within a date range."""
    employee_id: int
    hours: float
    calculated_wage: Decimal
