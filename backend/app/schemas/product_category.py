from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ProductCategoryResponse(BaseModel):
    id: int
    name: str
    sort_order: int

    class Config:
        from_attributes = True


class ProductCategoryCreate(BaseModel):
    name: str
    sort_order: int = 0
