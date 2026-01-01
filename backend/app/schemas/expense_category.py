from pydantic import BaseModel, Field
from typing import Optional


class ExpenseCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    parent_id: Optional[int] = None


class ExpenseCategoryCreate(ExpenseCategoryBase):
    pass


class ExpenseCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None


class ExpenseCategoryResponse(ExpenseCategoryBase):
    id: int
    level: int
    is_active: bool

    class Config:
        from_attributes = True


class ExpenseCategoryTree(ExpenseCategoryResponse):
    children: list["ExpenseCategoryTree"] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ExpenseCategoryLeafResponse(ExpenseCategoryResponse):
    """Response schema for leaf categories with full path."""
    full_path: str  # e.g., "Koszty operacyjne > Skladniki > Warzywa"
