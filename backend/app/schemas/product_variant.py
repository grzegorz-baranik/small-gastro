from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class ProductVariantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Nazwa wariantu (np. 'Maly', 'Duzy')")
    price: Decimal = Field(..., ge=0, description="Cena wariantu")


class ProductVariantCreate(ProductVariantBase):
    is_default: Optional[bool] = Field(False, description="Czy to domyslny wariant")


class ProductVariantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    price: Optional[Decimal] = Field(None, ge=0)
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class ProductVariantResponse(ProductVariantBase):
    id: int
    product_id: int
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductVariantListResponse(BaseModel):
    items: list[ProductVariantResponse]
    total: int


# Recipe ingredient schemas for variants
class VariantIngredientBase(BaseModel):
    ingredient_id: int
    quantity: Decimal = Field(..., gt=0, description="Ilosc skladnika (gramy lub sztuki)")
    is_primary: Optional[bool] = Field(False, description="Czy skladnik glowny (do obliczen marzy)")


class VariantIngredientCreate(VariantIngredientBase):
    pass


class VariantIngredientUpdate(BaseModel):
    quantity: Optional[Decimal] = Field(None, gt=0)
    is_primary: Optional[bool] = None


class VariantIngredientResponse(VariantIngredientBase):
    id: int
    ingredient_name: Optional[str] = None
    ingredient_unit_type: Optional[str] = None
    ingredient_unit_label: Optional[str] = None

    class Config:
        from_attributes = True


class VariantIngredientListResponse(BaseModel):
    items: list[VariantIngredientResponse]
    total: int


# Extended variant response with ingredients
class ProductVariantWithIngredientsResponse(ProductVariantResponse):
    ingredients: list[VariantIngredientResponse] = []
