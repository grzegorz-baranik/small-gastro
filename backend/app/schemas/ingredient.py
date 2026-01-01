from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.ingredient import UnitType


class IngredientBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    unit_type: UnitType
    unit_label: Optional[str] = Field(None, max_length=50, description="Jednostka wyswietlana (np. 'kg', 'szt', 'ml')")


class IngredientCreate(IngredientBase):
    current_stock_grams: Optional[float] = 0
    current_stock_count: Optional[int] = 0
    is_active: Optional[bool] = True


class IngredientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    unit_label: Optional[str] = Field(None, max_length=50)
    current_stock_grams: Optional[float] = None
    current_stock_count: Optional[int] = None
    is_active: Optional[bool] = None


class IngredientResponse(IngredientBase):
    id: int
    is_active: bool
    current_stock_grams: float
    current_stock_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IngredientListResponse(BaseModel):
    items: list[IngredientResponse]
    total: int
