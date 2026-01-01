from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.models.inventory_snapshot import SnapshotType


class InventorySnapshotCreate(BaseModel):
    ingredient_id: int
    quantity_grams: Optional[Decimal] = None
    quantity_count: Optional[int] = None


class InventorySnapshotResponse(BaseModel):
    id: int
    daily_record_id: int
    ingredient_id: int
    ingredient_name: Optional[str] = None
    snapshot_type: SnapshotType
    quantity_grams: Optional[Decimal] = None
    quantity_count: Optional[int] = None
    recorded_at: datetime

    class Config:
        from_attributes = True


class InventoryDiscrepancy(BaseModel):
    ingredient_id: int
    ingredient_name: str
    unit_type: str
    opening_quantity: Decimal
    closing_quantity: Decimal
    actual_used: Decimal
    expected_used: Decimal
    discrepancy: Decimal
    discrepancy_percent: Optional[Decimal] = None


class CurrentStock(BaseModel):
    ingredient_id: int
    ingredient_name: str
    unit_type: str
    current_stock: Decimal
