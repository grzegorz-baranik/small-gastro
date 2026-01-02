from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from decimal import Decimal


class ProductIngredientBase(BaseModel):
    ingredient_id: int
    quantity: Decimal = Field(..., gt=0)
    is_primary: bool = False


class ProductIngredientCreate(ProductIngredientBase):
    pass


class ProductIngredientUpdate(BaseModel):
    quantity: Decimal = Field(..., gt=0)
    is_primary: Optional[bool] = None


class ProductIngredientResponse(ProductIngredientBase):
    id: int
    ingredient_name: Optional[str] = None
    ingredient_unit_type: Optional[str] = None

    class Config:
        from_attributes = True


class ProductVariantBase(BaseModel):
    name: Optional[str] = Field(None, max_length=50)  # NULL for single-size products
    price_pln: Decimal = Field(..., gt=0)


class ProductVariantCreate(ProductVariantBase):
    ingredients: Optional[list[ProductIngredientCreate]] = []


class ProductVariantUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    price_pln: Optional[Decimal] = Field(None, gt=0)
    is_active: Optional[bool] = None


class ProductVariantResponse(ProductVariantBase):
    id: int
    is_active: bool
    ingredients: list[ProductIngredientResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class ProductCreate(ProductBase):
    has_variants: bool = False
    variants: list[ProductVariantCreate] = []


class ProductSimpleCreate(BaseModel):
    """Simplified product creation with single price (creates one variant)."""
    name: str = Field(..., min_length=1, max_length=255)
    price_pln: Decimal = Field(..., gt=0)
    ingredients: Optional[list[ProductIngredientCreate]] = []


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: int
    has_variants: bool
    is_active: bool
    sort_order: int
    variants: list[ProductVariantResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int


class ProductReorderRequest(BaseModel):
    """Request to reorder products."""
    product_ids: list[int] = Field(..., min_length=1, description="Lista ID produktow w nowej kolejnosci")

    @field_validator('product_ids')
    @classmethod
    def validate_unique_ids(cls, v):
        if len(v) != len(set(v)):
            raise ValueError("Lista zawiera duplikaty ID")
        return v


class ProductReorderResponse(BaseModel):
    """Response from reorder operation."""
    message: str
    updated_count: int
