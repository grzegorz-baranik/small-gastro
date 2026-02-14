from sqlalchemy import Column, Integer, Date, Time, Boolean, DateTime, ForeignKey, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.core.database import Base


class ShiftScheduleOverride(Base):
    """
    Represents a schedule override for a specific date.

    An override replaces the recurring template for a specific date.
    Use cases:
    - Change shift hours for a specific day (e.g., Anna works 09:00-17:00 on 2026-01-05 instead of usual 08:00-16:00)
    - Mark an employee as having the day off (is_day_off=True)
    - Add an extra shift for an employee who doesn't have a template for that day

    Constraints:
    - One employee can only have one override per date (unique_override_per_date)
    - If not a day off, times must be provided
    - If not a day off, end time must be after start time
    """
    __tablename__ = "shift_schedule_overrides"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(
        Integer,
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False
    )
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=True)  # NULL when is_day_off=True
    end_time = Column(Time, nullable=True)    # NULL when is_day_off=True
    is_day_off = Column(Boolean, nullable=False, server_default="false")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('employee_id', 'date', name='unique_override_per_date'),
        CheckConstraint(
            '(is_day_off = true) OR (start_time IS NOT NULL AND end_time IS NOT NULL AND end_time > start_time)',
            name='override_valid_times'
        ),
        Index("idx_schedule_overrides_employee", "employee_id"),
        Index("idx_schedule_overrides_date", "date"),
    )

    # Relationships
    employee = relationship("Employee", back_populates="schedule_overrides")

    @property
    def hours(self) -> float:
        """
        Calculate shift duration in hours.
        Returns 0 if day off or times not set.
        """
        if self.is_day_off or self.start_time is None or self.end_time is None:
            return 0.0
        start = datetime.combine(datetime.min, self.start_time)
        end = datetime.combine(datetime.min, self.end_time)
        delta = end - start
        return delta.total_seconds() / 3600
