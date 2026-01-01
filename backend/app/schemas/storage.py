from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class StorageInventoryBase(BaseModel):
    ingredient_id: int
    quantity_grams: Optional[Decimal] = Field(None, ge=0, description="Ilosc w gramach (dla skladnikow wagowych)")
    quantity_count: Optional[int] = Field(None, ge=0, description="Ilosc w sztukach (dla skladnikow zliczanych)")


class StorageInventoryCreate(StorageInventoryBase):
    notes: Optional[str] = Field(None, max_length=500, description="Notatki do zliczenia")


class StorageInventoryResponse(StorageInventoryBase):
    id: int
    ingredient_name: Optional[str] = None
    ingredient_unit_type: Optional[str] = None
    ingredient_unit_label: Optional[str] = None
    notes: Optional[str] = None
    recorded_at: datetime
    recorded_by: Optional[str] = None

    class Config:
        from_attributes = True


class StorageInventoryListResponse(BaseModel):
    items: list[StorageInventoryResponse]
    total: int


# Bulk count request for multiple ingredients at once
class StorageCountItem(BaseModel):
    ingredient_id: int
    quantity_grams: Optional[Decimal] = Field(None, ge=0)
    quantity_count: Optional[int] = Field(None, ge=0)


class StorageCountBulkCreate(BaseModel):
    items: list[StorageCountItem]
    notes: Optional[str] = Field(None, max_length=500)


class StorageCountBulkResponse(BaseModel):
    items: list[StorageInventoryResponse]
    recorded_at: datetime


# Current storage status
class StorageCurrentStatus(BaseModel):
    ingredient_id: int
    ingredient_name: str
    ingredient_unit_type: str
    ingredient_unit_label: Optional[str] = None
    current_quantity: Decimal
    last_count_at: Optional[datetime] = None
    is_active: bool
