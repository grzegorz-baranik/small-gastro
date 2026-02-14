from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class ProductVariantBase(BaseModel):
    name: Optional[str] = Field(None, max_length=50, description="Nazwa wariantu (np. 'Maly', 'Duzy') - NULL dla produktow bez wariantow")
    price_pln: Decimal = Field(..., gt=0, description="Cena wariantu w PLN")


class ProductVariantCreate(ProductVariantBase):
    is_default: Optional[bool] = Field(False, description="Czy to domyslny wariant")


class ProductVariantUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    price_pln: Optional[Decimal] = Field(None, gt=0)
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class ProductVariantResponse(ProductVariantBase):
    id: int
    product_id: int
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


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


# Extended variant response with ingredients (must be defined before ProductVariantListResponse)
class ProductVariantWithIngredientsResponse(ProductVariantResponse):
    ingredients: list[VariantIngredientResponse] = []


# List response using the extended response type
class ProductVariantListResponse(BaseModel):
    items: list[ProductVariantWithIngredientsResponse]
    total: int
