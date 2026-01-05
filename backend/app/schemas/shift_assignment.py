from pydantic import BaseModel, Field, field_validator
from datetime import time
from decimal import Decimal


class ShiftAssignmentBase(BaseModel):
    """Base schema for shift assignment data."""
    employee_id: int
    start_time: time
    end_time: time

    @field_validator('end_time')
    @classmethod
    def validate_end_time(cls, v: time, info) -> time:
        """Validate that end_time is after start_time."""
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('Godzina zakonczenia musi byc po godzinie rozpoczecia')
        return v


class ShiftAssignmentCreate(ShiftAssignmentBase):
    """Schema for creating a new shift assignment."""
    pass


class ShiftAssignmentUpdate(BaseModel):
    """Schema for updating a shift assignment (only times can be changed)."""
    start_time: time
    end_time: time

    @field_validator('end_time')
    @classmethod
    def validate_end_time(cls, v: time, info) -> time:
        """Validate that end_time is after start_time."""
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('Godzina zakonczenia musi byc po godzinie rozpoczecia')
        return v


class ShiftAssignmentResponse(BaseModel):
    """Schema for shift assignment response with employee details."""
    id: int
    employee_id: int
    employee_name: str
    start_time: time
    end_time: time
    hours_worked: float
    hourly_rate: Decimal

    class Config:
        from_attributes = True


class ShiftAssignmentListResponse(BaseModel):
    """Schema for list of shift assignments."""
    items: list[ShiftAssignmentResponse]
    total: int
