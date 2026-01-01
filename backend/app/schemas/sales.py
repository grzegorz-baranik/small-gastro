from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class SalesItemCreate(BaseModel):
    product_id: int
    quantity_sold: int = Field(..., gt=0)


class SalesItemResponse(BaseModel):
    id: int
    daily_record_id: int
    product_id: int
    product_name: Optional[str] = None
    quantity_sold: int
    unit_price: Decimal
    total_price: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class DailySalesSummary(BaseModel):
    daily_record_id: int
    date: str
    items: list[SalesItemResponse]
    total_items_sold: int
    total_revenue: Decimal
