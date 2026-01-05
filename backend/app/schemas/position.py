from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal


class PositionBase(BaseModel):
    """Base schema for position data."""
    name: str = Field(..., min_length=1, max_length=100)
    hourly_rate: Decimal = Field(..., gt=0)


class PositionCreate(PositionBase):
    """Schema for creating a new position."""
    pass


class PositionUpdate(BaseModel):
    """Schema for updating a position. All fields are optional."""
    name: str | None = Field(None, min_length=1, max_length=100)
    hourly_rate: Decimal | None = Field(None, gt=0)


class PositionResponse(BaseModel):
    """Schema for position response with employee count."""
    id: int
    name: str
    hourly_rate: Decimal
    employee_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class PositionListResponse(BaseModel):
    """Schema for paginated position list."""
    items: list[PositionResponse]
    total: int
