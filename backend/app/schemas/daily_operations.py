"""
Schemas for daily operations: opening/closing day, inventory snapshots, usage calculations.

These schemas support the redesigned inventory system with unified quantity field
and location-aware snapshots.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date, datetime
from decimal import Decimal

from app.models.daily_record import DayStatus
from app.models.inventory_snapshot import SnapshotType, InventoryLocation


# -----------------------------------------------------------------------------
# Inventory Snapshot Items (used in requests)
# -----------------------------------------------------------------------------

class InventorySnapshotItem(BaseModel):
    """
    Single ingredient quantity for opening/closing inventory.
    Uses unified quantity field (in ingredient's native unit: kg or count).
    """
    ingredient_id: int
    quantity: Decimal = Field(..., ge=0, description="Ilosc w jednostce skladnika (kg lub szt)")

    @field_validator("quantity", mode="before")
    @classmethod
    def coerce_quantity(cls, v):
        if v is None:
            return Decimal("0")
        return Decimal(str(v))


class InventorySnapshotResponse(BaseModel):
    """Response for a single inventory snapshot."""
    id: int
    daily_record_id: int
    ingredient_id: int
    ingredient_name: str
    unit_label: str
    snapshot_type: SnapshotType
    location: InventoryLocation
    quantity: Decimal
    recorded_at: datetime

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------------
# Open Day
# -----------------------------------------------------------------------------

class OpenDayRequest(BaseModel):
    """Request to open a new day with opening inventory counts."""
    date: Optional[date] = None
    opening_inventory: list[InventorySnapshotItem] = Field(
        default_factory=list,
        description="Lista stanow poczatkowych skladnikow"
    )

    @field_validator("date", mode="before")
    @classmethod
    def default_to_today(cls, v):
        if v is None:
            return date.today()
        return v


class PreviousDayWarning(BaseModel):
    """Warning when previous day is not closed."""
    previous_date: date
    previous_record_id: int
    message: str = "Poprzedni dzien nie zostal zamkniety"


class OpenDayResponse(BaseModel):
    """Response after successfully opening a day."""
    id: int
    date: date
    status: DayStatus
    opened_at: datetime
    opening_snapshots: list[InventorySnapshotResponse] = []
    previous_day_warning: Optional[PreviousDayWarning] = None

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------------
# Close Day
# -----------------------------------------------------------------------------

class CloseDayRequest(BaseModel):
    """Request to close an open day with closing inventory counts."""
    closing_inventory: list[InventorySnapshotItem] = Field(
        default_factory=list,
        description="Lista stanow koncowych skladnikow"
    )
    notes: Optional[str] = Field(None, max_length=1000, description="Notatki do dnia")


class UsageItem(BaseModel):
    """Calculated usage for a single ingredient during the day."""
    ingredient_id: int
    ingredient_name: str
    unit_label: str
    opening: Decimal
    deliveries: Decimal
    transfers: Decimal
    spoilage: Decimal
    closing: Decimal
    usage: Decimal  # Opening + Deliveries + Transfers - Spoilage - Closing
    expected: Decimal  # Expected closing (Opening + Deliveries + Transfers - Spoilage)


class CloseDayResponse(BaseModel):
    """Response after successfully closing a day."""
    id: int
    date: date
    status: DayStatus
    opened_at: datetime
    closed_at: Optional[datetime]
    notes: Optional[str]
    usage_summary: list[UsageItem] = []

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------------
# Day Summary
# -----------------------------------------------------------------------------

class DeliverySummaryItem(BaseModel):
    """Summary of a delivery for the day."""
    id: int
    ingredient_id: int
    ingredient_name: str
    unit_label: str
    quantity: Decimal
    price_pln: Decimal
    delivered_at: datetime


class TransferSummaryItem(BaseModel):
    """Summary of a storage transfer for the day."""
    id: int
    ingredient_id: int
    ingredient_name: str
    unit_label: str
    quantity: Decimal
    transferred_at: datetime


class SpoilageSummaryItem(BaseModel):
    """Summary of spoilage for the day."""
    id: int
    ingredient_id: int
    ingredient_name: str
    unit_label: str
    quantity: Decimal
    reason: str
    notes: Optional[str]
    recorded_at: datetime


class MidDayEventsSummary(BaseModel):
    """Summary of all mid-day events (deliveries, transfers, spoilage)."""
    deliveries: list[DeliverySummaryItem] = []
    deliveries_count: int = 0
    deliveries_total_pln: Decimal = Decimal("0")
    transfers: list[TransferSummaryItem] = []
    transfers_count: int = 0
    spoilages: list[SpoilageSummaryItem] = []
    spoilages_count: int = 0


class DayEventsSummary(BaseModel):
    """Simplified events summary matching frontend type."""
    deliveries_count: int = 0
    deliveries_total_pln: Decimal = Decimal("0")
    transfers_count: int = 0
    spoilage_count: int = 0


class UsageItemResponse(BaseModel):
    """Usage item for day summary response - matches frontend UsageItem type."""
    ingredient_id: int
    ingredient_name: str
    unit_type: str
    unit_label: str
    opening_quantity: Decimal
    deliveries_quantity: Decimal
    transfers_quantity: Decimal
    spoilage_quantity: Decimal
    expected_closing: Decimal
    closing_quantity: Optional[Decimal]
    usage: Optional[Decimal]
    expected_usage: Optional[Decimal]
    discrepancy: Optional[Decimal]
    discrepancy_percent: Optional[Decimal]
    discrepancy_level: Optional[str]  # 'ok' | 'warning' | 'critical'


class CalculatedSaleItem(BaseModel):
    """Calculated sale item (Phase 4 feature)."""
    product_id: int
    product_name: str
    variant_id: Optional[int]
    variant_name: Optional[str]
    quantity_sold: Decimal
    unit_price_pln: Decimal
    revenue_pln: Decimal


class DiscrepancyAlert(BaseModel):
    """Discrepancy alert (Phase 4 feature)."""
    ingredient_id: int
    ingredient_name: str
    discrepancy_percent: Decimal
    level: str  # 'ok' | 'warning' | 'critical'
    message: str


class DailyRecordSummary(BaseModel):
    """Daily record info for summary response."""
    id: int
    date: date
    status: DayStatus
    opened_at: datetime
    closed_at: Optional[datetime]
    notes: Optional[str]
    total_income_pln: Optional[Decimal]
    total_delivery_cost_pln: Optional[Decimal]
    total_spoilage_cost_pln: Optional[Decimal]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DaySummaryResponse(BaseModel):
    """Full summary of a day's operations - matches frontend DaySummaryResponse type."""
    daily_record: DailyRecordSummary
    opening_time: Optional[str]
    closing_time: Optional[str]
    events: DayEventsSummary
    usage_items: list[UsageItemResponse] = []
    calculated_sales: list[CalculatedSaleItem] = []
    total_income_pln: Decimal = Decimal("0")
    discrepancy_alerts: list[DiscrepancyAlert] = []

    class Config:
        from_attributes = True


class DaySummaryInternalResponse(BaseModel):
    """Internal summary response with full details for backend use."""
    id: int
    date: date
    status: DayStatus
    opened_at: datetime
    closed_at: Optional[datetime]
    notes: Optional[str]

    # Inventory snapshots
    opening_snapshots: list[InventorySnapshotResponse] = []
    closing_snapshots: list[InventorySnapshotResponse] = []

    # Mid-day events
    mid_day_events: MidDayEventsSummary = MidDayEventsSummary()

    # Usage calculations (available when day is closed)
    usage_summary: list[UsageItem] = []

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------------
# Previous Closing (for pre-filling opening counts)
# -----------------------------------------------------------------------------

class PreviousClosingItem(BaseModel):
    """Previous closing quantity for an ingredient."""
    ingredient_id: int
    ingredient_name: str
    unit_label: str
    is_active: bool
    quantity: Decimal
    closed_date: date


class PreviousClosingResponse(BaseModel):
    """Response containing previous day's closing inventory for pre-fill."""
    previous_date: Optional[date] = None
    previous_record_id: Optional[int] = None
    items: list[PreviousClosingItem] = []
    message: Optional[str] = None


# -----------------------------------------------------------------------------
# Edit Closed Day
# -----------------------------------------------------------------------------

class EditClosedDayRequest(BaseModel):
    """Request to edit a closed day's closing inventory."""
    closing_inventory: list[InventorySnapshotItem] = Field(
        default_factory=list,
        description="Zaktualizowana lista stanow koncowych"
    )
    notes: Optional[str] = Field(None, max_length=1000)


class EditClosedDayResponse(BaseModel):
    """Response after editing a closed day."""
    id: int
    date: date
    status: DayStatus
    updated_at: datetime
    usage_summary: list[UsageItem] = []
    message: str = "Dzien zostal zaktualizowany"

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------------
# Day Detail (GET /daily-records/{id})
# -----------------------------------------------------------------------------

class DailyRecordDetailResponse(BaseModel):
    """Detailed response for a single daily record."""
    id: int
    date: date
    status: DayStatus
    opened_at: datetime
    closed_at: Optional[datetime]
    notes: Optional[str]
    total_income_pln: Optional[Decimal]
    total_delivery_cost_pln: Decimal
    total_spoilage_cost_pln: Decimal
    created_at: datetime
    updated_at: datetime

    # Related data
    opening_snapshots: list[InventorySnapshotResponse] = []
    closing_snapshots: list[InventorySnapshotResponse] = []
    mid_day_events: MidDayEventsSummary = MidDayEventsSummary()

    class Config:
        from_attributes = True
