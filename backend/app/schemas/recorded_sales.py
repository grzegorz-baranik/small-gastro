from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional
from enum import Enum


class VoidReason(str, Enum):
    MISTAKE = "mistake"
    CUSTOMER_REFUND = "customer_refund"
    DUPLICATE = "duplicate"
    OTHER = "other"


class RecordedSaleCreate(BaseModel):
    product_variant_id: int
    quantity: int = Field(default=1, ge=1, le=100)


class RecordedSaleVoid(BaseModel):
    reason: VoidReason
    notes: Optional[str] = Field(None, max_length=255)


class RecordedSaleResponse(BaseModel):
    id: int
    daily_record_id: int
    product_variant_id: int
    product_name: str
    variant_name: Optional[str]
    shift_assignment_id: Optional[int]
    quantity: int
    unit_price_pln: Decimal
    total_pln: Decimal
    recorded_at: datetime
    voided_at: Optional[datetime]
    void_reason: Optional[str]
    void_notes: Optional[str]

    class Config:
        from_attributes = True


class DaySalesTotal(BaseModel):
    total_pln: Decimal
    sales_count: int
    items_count: int
