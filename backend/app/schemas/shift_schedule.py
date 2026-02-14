"""
Pydantic schemas for schedule override and weekly schedule operations.

Schedule overrides allow modifying shift patterns for specific dates.
Weekly schedule aggregates templates and overrides for calendar display.
"""
from pydantic import BaseModel, Field, model_validator
from datetime import date, time
from typing import Optional


class ScheduleOverrideCreate(BaseModel):
    """Schema for creating/updating a schedule override."""
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_day_off: bool = False

    @model_validator(mode='after')
    def validate_times(self) -> 'ScheduleOverrideCreate':
        if not self.is_day_off:
            if self.start_time is None or self.end_time is None:
                raise ValueError('start_time and end_time are required when not a day off')
            if self.end_time <= self.start_time:
                raise ValueError('end_time must be after start_time')
        return self


class ScheduleOverrideResponse(BaseModel):
    """Schema for schedule override response."""
    id: int
    employee_id: int
    employee_name: str
    date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_day_off: bool
    is_override: bool = True  # Always true for override responses

    class Config:
        from_attributes = True


class DayShift(BaseModel):
    """A single shift entry for a day in the weekly schedule."""
    employee_id: int
    employee_name: str
    start_time: time
    end_time: time
    source: str = Field(..., description="'template' or 'override'")
    is_override: bool = False
    employee_inactive: Optional[bool] = None
    warning: Optional[str] = None


class DaySchedule(BaseModel):
    """Schedule for a single day including all shifts."""
    date: date
    day_of_week: int
    day_name: str
    shifts: list[DayShift]


class WeeklyScheduleResponse(BaseModel):
    """Schema for weekly schedule response."""
    week_start: date
    week_end: date
    schedules: list[DaySchedule]
