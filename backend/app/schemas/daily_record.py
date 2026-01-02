from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from app.models.daily_record import DayStatus
from app.schemas.inventory import InventorySnapshotCreate, InventoryDiscrepancy


class DailyRecordCreate(BaseModel):
    date: date
    notes: Optional[str] = None
    opening_inventory: list[InventorySnapshotCreate] = []


class DailyRecordClose(BaseModel):
    notes: Optional[str] = None
    closing_inventory: list[InventorySnapshotCreate] = []


class DailyRecordResponse(BaseModel):
    id: int
    date: date
    status: DayStatus
    opened_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DailyRecordSummary(DailyRecordResponse):
    total_sales: Decimal = Decimal("0")
    total_revenue: Decimal = Decimal("0")
    total_expenses: Decimal = Decimal("0")
    items_sold: int = 0
    discrepancies: list[InventoryDiscrepancy] = []
