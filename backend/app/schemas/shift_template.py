"""
Pydantic schemas for shift template operations.

Shift templates define recurring weekly shift patterns for employees.
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime, time
from typing import Optional


# Polish day names (0=Monday, 6=Sunday)
DAY_NAMES = [
    "Poniedzialek",
    "Wtorek",
    "Sroda",
    "Czwartek",
    "Piatek",
    "Sobota",
    "Niedziela",
]


class EmployeeMinimal(BaseModel):
    """Minimal employee info for embedding in template response."""
    id: int
    name: str

    class Config:
        from_attributes = True


class ShiftTemplateBase(BaseModel):
    """Base schema for shift template data."""
    employee_id: int
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
    start_time: time
    end_time: time


class ShiftTemplateCreate(ShiftTemplateBase):
    """Schema for creating a new shift template."""

    @field_validator('day_of_week')
    @classmethod
    def validate_day_of_week(cls, v: int) -> int:
        if v < 0 or v > 6:
            raise ValueError('day_of_week must be between 0 (Monday) and 6 (Sunday)')
        return v

    @model_validator(mode='after')
    def validate_time_range(self) -> 'ShiftTemplateCreate':
        if self.end_time <= self.start_time:
            raise ValueError('end_time must be after start_time')
        return self


class ShiftTemplateUpdate(BaseModel):
    """Schema for updating a shift template. All fields are optional."""
    start_time: Optional[time] = None
    end_time: Optional[time] = None

    @model_validator(mode='after')
    def validate_time_range(self) -> 'ShiftTemplateUpdate':
        if self.start_time is not None and self.end_time is not None:
            if self.end_time <= self.start_time:
                raise ValueError('end_time must be after start_time')
        return self


class ShiftTemplateResponse(BaseModel):
    """Schema for shift template response."""
    id: int
    employee_id: int
    employee_name: str
    day_of_week: int
    day_name: str
    start_time: time
    end_time: time
    created_at: datetime
    employee: Optional[EmployeeMinimal] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_day_name(cls, template, employee_name: str) -> 'ShiftTemplateResponse':
        """Create response from ORM model with computed day_name."""
        return cls(
            id=template.id,
            employee_id=template.employee_id,
            employee_name=employee_name,
            day_of_week=template.day_of_week,
            day_name=DAY_NAMES[template.day_of_week],
            start_time=template.start_time,
            end_time=template.end_time,
            created_at=template.created_at,
            employee=EmployeeMinimal(id=template.employee.id, name=template.employee.name) if template.employee else None,
        )


class ShiftTemplateListResponse(BaseModel):
    """Schema for paginated shift template list."""
    items: list[ShiftTemplateResponse]
    total: int
