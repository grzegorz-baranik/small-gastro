from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal


class EmployeeBase(BaseModel):
    """Base schema for employee data."""
    name: str = Field(..., min_length=1, max_length=200)
    position_id: int
    hourly_rate: Decimal | None = Field(None, gt=0)


class EmployeeCreate(EmployeeBase):
    """Schema for creating a new employee."""
    is_active: bool = True


class EmployeeUpdate(BaseModel):
    """Schema for updating an employee. All fields are optional."""
    name: str | None = Field(None, min_length=1, max_length=200)
    position_id: int | None = None
    hourly_rate: Decimal | None = Field(None, gt=0)


class EmployeeResponse(BaseModel):
    """Schema for employee response with position details."""
    id: int
    name: str
    position_id: int
    position_name: str
    hourly_rate: Decimal  # Effective rate (override or position default)
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class EmployeeListResponse(BaseModel):
    """Schema for paginated employee list."""
    items: list[EmployeeResponse]
    total: int
