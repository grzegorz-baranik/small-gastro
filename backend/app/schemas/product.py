from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class ProductIngredientBase(BaseModel):
    ingredient_id: int
    quantity: Decimal = Field(..., gt=0)


class ProductIngredientCreate(ProductIngredientBase):
    pass


class ProductIngredientUpdate(BaseModel):
    quantity: Decimal = Field(..., gt=0)


class ProductIngredientResponse(ProductIngredientBase):
    id: int
    ingredient_name: Optional[str] = None
    ingredient_unit_type: Optional[str] = None

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    price: Decimal = Field(..., ge=0)


class ProductCreate(ProductBase):
    ingredients: Optional[list[ProductIngredientCreate]] = []


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    price: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: int
    is_active: bool
    ingredients: list[ProductIngredientResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
