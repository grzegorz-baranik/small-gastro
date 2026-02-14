"""
Pydantic schemas for batch/expiry tracking.

Provides request/response schemas for:
- Batch management (create, read)
- Batch deductions (audit trail)
- Expiry alerts
- FIFO inventory display
"""

from pydantic import BaseModel, Field, field_validator, computed_field
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------

class AlertLevel(str, Enum):
    """Expiry alert severity levels."""
    EXPIRED = "expired"      # Already expired
    CRITICAL = "critical"    # 0-2 days until expiry
    WARNING = "warning"      # 3-7 days until expiry


class BatchLocation(str, Enum):
    """Location where batch is stored."""
    STORAGE = "storage"
    SHOP = "shop"


class DeductionReason(str, Enum):
    """Reasons for batch quantity deduction."""
    SALES = "sales"
    SPOILAGE = "spoilage"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"


# -----------------------------------------------------------------------------
# Alert thresholds (module-level constants)
# -----------------------------------------------------------------------------

EXPIRY_ALERT_DAYS = 7
EXPIRY_CRITICAL_DAYS = 2


# -----------------------------------------------------------------------------
# Batch Create/Update Schemas
# -----------------------------------------------------------------------------

class BatchCreate(BaseModel):
    """
    Request schema for manual batch creation (rare case).
    Usually batches are auto-created from deliveries.
    """
    ingredient_id: int = Field(..., description="ID skladnika")
    expiry_date: Optional[date] = Field(None, description="Data waznosci")
    initial_quantity: Decimal = Field(..., gt=0, description="Poczatkowa ilosc")
    location: BatchLocation = Field(default=BatchLocation.STORAGE, description="Lokalizacja")
    notes: Optional[str] = Field(None, max_length=500, description="Notatki")

    @field_validator("initial_quantity", mode="before")
    @classmethod
    def coerce_quantity(cls, v):
        if v is None:
            return Decimal("0")
        return Decimal(str(v))


# -----------------------------------------------------------------------------
# Batch Response Schemas
# -----------------------------------------------------------------------------

class BatchResponse(BaseModel):
    """
    Response schema for a single batch with calculated fields.

    Includes:
    - days_until_expiry: Calculated from expiry_date
    - is_expiring_soon: True if <= EXPIRY_ALERT_DAYS
    - age_days: Days since batch was created
    """
    id: int
    batch_number: str
    ingredient_id: int
    ingredient_name: str
    unit_label: str
    delivery_item_id: Optional[int] = None
    expiry_date: Optional[date] = None
    initial_quantity: Decimal
    remaining_quantity: Decimal
    location: str
    is_active: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Calculated fields
    days_until_expiry: Optional[int] = None
    is_expiring_soon: bool = False
    age_days: int = 0

    class Config:
        from_attributes = True

    @computed_field
    @property
    def usage_percentage(self) -> Decimal:
        """Percentage of initial quantity that has been used."""
        if self.initial_quantity <= 0:
            return Decimal("0")
        used = self.initial_quantity - self.remaining_quantity
        return (used / self.initial_quantity * 100).quantize(Decimal("0.1"))


class BatchListResponse(BaseModel):
    """Response schema for a list of batches."""
    items: list[BatchResponse] = []
    total: int = 0
    expiring_soon_count: int = 0


# -----------------------------------------------------------------------------
# Batch Deduction Schemas
# -----------------------------------------------------------------------------

class BatchDeductionCreate(BaseModel):
    """Request schema for deducting from a batch."""
    batch_id: int = Field(..., description="ID partii")
    quantity: Decimal = Field(..., gt=0, description="Ilosc do odjecia")
    reason: DeductionReason = Field(..., description="Przyczyna odliczenia")
    daily_record_id: Optional[int] = Field(None, description="ID dnia (opcjonalne)")
    reference_type: Optional[str] = Field(None, description="Typ powiazanego rekordu")
    reference_id: Optional[int] = Field(None, description="ID powiazanego rekordu")
    notes: Optional[str] = Field(None, max_length=500, description="Notatki")

    @field_validator("quantity", mode="before")
    @classmethod
    def coerce_quantity(cls, v):
        if v is None:
            return Decimal("0")
        return Decimal(str(v))


class BatchDeductionResponse(BaseModel):
    """Response schema for a batch deduction."""
    id: int
    batch_id: int
    batch_number: str
    daily_record_id: Optional[int] = None
    quantity: Decimal
    reason: str
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------------
# Expiry Alert Schemas
# -----------------------------------------------------------------------------

class ExpiryAlertResponse(BaseModel):
    """
    Response schema for a single expiry alert.

    alert_level indicates severity:
    - expired: Already past expiry date
    - critical: 0-2 days until expiry
    - warning: 3-7 days until expiry
    """
    batch_id: int
    batch_number: str
    ingredient_id: int
    ingredient_name: str
    unit_label: str
    expiry_date: date
    remaining_quantity: Decimal
    location: str
    days_until_expiry: int
    alert_level: AlertLevel

    class Config:
        from_attributes = True


class ExpiryAlertsListResponse(BaseModel):
    """Response schema for expiry alerts list with summary counts."""
    alerts: list[ExpiryAlertResponse] = []
    total: int = 0
    expired_count: int = 0
    critical_count: int = 0
    warning_count: int = 0


# -----------------------------------------------------------------------------
# FIFO Inventory Display Schemas
# -----------------------------------------------------------------------------

class BatchInventoryItem(BaseModel):
    """
    Schema for FIFO display of a batch in inventory.

    fifo_order indicates the order in which batches should be used
    (1 = use first, based on oldest created_at).
    """
    id: int
    batch_number: str
    expiry_date: Optional[date] = None
    remaining_quantity: Decimal
    location: str
    is_active: bool
    created_at: datetime
    fifo_order: int = 0  # 1 = use first (oldest)
    days_until_expiry: Optional[int] = None
    is_expiring_soon: bool = False

    class Config:
        from_attributes = True


class IngredientBatchSummary(BaseModel):
    """
    Summary of all batches for a specific ingredient.

    Useful for inventory display with FIFO ordering.
    """
    ingredient_id: int
    ingredient_name: str
    unit_label: str
    total_quantity: Decimal
    active_batch_count: int
    expiring_soon_count: int
    batches: list[BatchInventoryItem] = []

    class Config:
        from_attributes = True
