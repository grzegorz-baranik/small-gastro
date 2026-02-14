"""
Schemas for Day Wizard functionality.

Provides structured data models for the wizard flow:
- Opening step (shifts + inventory)
- Mid-day operations
- Closing step (sales preview + confirmation)
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum

from app.models.inventory_snapshot import InventoryLocation
from app.models.daily_record import DayStatus


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------


class WizardStep(str, Enum):
    """Wizard step identifiers."""
    OPENING = "opening"
    MID_DAY = "mid_day"
    CLOSING = "closing"
    COMPLETED = "completed"


class DiscrepancyLevel(str, Enum):
    """Discrepancy severity levels."""
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"


# -----------------------------------------------------------------------------
# Input Schemas
# -----------------------------------------------------------------------------


class ConfirmedShiftInput(BaseModel):
    """Input for confirming a shift assignment."""
    employee_id: int
    start_time: time
    end_time: time

    @field_validator('end_time')
    @classmethod
    def validate_end_time(cls, v: time, info) -> time:
        """Validate that end_time is after start_time."""
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('Godzina zakonczenia musi byc po godzinie rozpoczecia')
        return v


class OpeningInventoryInput(BaseModel):
    """Input for opening inventory entry."""
    ingredient_id: int
    quantity: Decimal = Field(..., ge=0)
    location: InventoryLocation = InventoryLocation.SHOP


class CompleteOpeningRequest(BaseModel):
    """Request to complete the opening step."""
    confirmed_shifts: list[ConfirmedShiftInput]
    opening_inventory: list[OpeningInventoryInput]


class SalesPreviewRequest(BaseModel):
    """Request for sales preview calculation."""
    closing_inventory: dict[int, Decimal]  # ingredient_id -> quantity


# -----------------------------------------------------------------------------
# State Schemas (Sub-components of WizardStateResponse)
# -----------------------------------------------------------------------------


class OpeningStepState(BaseModel):
    """State of the opening step."""
    completed: bool = False
    inventory_entered: bool = False
    shifts_confirmed: bool = False
    shift_count: int = 0


class MidDayStepState(BaseModel):
    """State of the mid-day step."""
    deliveries_count: int = 0
    transfers_count: int = 0
    spoilage_count: int = 0
    total_delivery_cost_pln: Decimal = Decimal("0")


class ClosingStepState(BaseModel):
    """State of the closing step."""
    closing_inventory_entered: bool = False
    has_discrepancies: bool = False
    critical_discrepancy_count: int = 0
    warning_discrepancy_count: int = 0


# -----------------------------------------------------------------------------
# Output Schemas
# -----------------------------------------------------------------------------


class SuggestedShift(BaseModel):
    """Suggested shift from template or schedule."""
    employee_id: int
    employee_name: str
    position_name: str
    start_time: time
    end_time: time
    source: str  # "template", "override", "manual"


class SuggestedShiftsResponse(BaseModel):
    """Response with list of suggested shifts."""
    suggested_shifts: list[SuggestedShift]


class IngredientUsage(BaseModel):
    """Ingredient usage calculation result."""
    ingredient_id: int
    ingredient_name: str
    unit_type: str
    unit_label: str
    opening: Decimal
    deliveries: Decimal = Decimal("0")
    transfers: Decimal = Decimal("0")
    spoilage: Decimal = Decimal("0")
    closing: Decimal
    expected: Decimal  # Opening + Deliveries + Transfers - Spoilage
    used: Decimal  # Expected - Closing (or Opening + ... - Closing)
    discrepancy_percent: Optional[Decimal] = None
    discrepancy_level: DiscrepancyLevel = DiscrepancyLevel.OK


class CalculatedSale(BaseModel):
    """Calculated sale from ingredient usage."""
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal
    total_revenue: Decimal


class SalesPreviewSummary(BaseModel):
    """Summary of sales preview."""
    total_revenue_pln: Decimal = Decimal("0")
    total_delivery_cost_pln: Decimal = Decimal("0")
    gross_profit_pln: Decimal = Decimal("0")


class SalesPreviewResponse(BaseModel):
    """Response for sales preview endpoint."""
    ingredients_used: list[IngredientUsage]
    calculated_sales: list[CalculatedSale]
    summary: SalesPreviewSummary
    warnings: list[str] = []


class WizardStateResponse(BaseModel):
    """Complete wizard state response."""
    daily_record_id: int
    date: date
    status: DayStatus
    current_step: Optional[WizardStep]
    opening: OpeningStepState
    mid_day: MidDayStepState
    closing: ClosingStepState

    # Additional context
    opened_at: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class CompleteOpeningResponse(BaseModel):
    """Response after completing opening step."""
    daily_record_id: int
    current_step: WizardStep
    opening: OpeningStepState
    message: str = "Otwarcie dnia zakonczone pomyslnie"
