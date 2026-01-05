from sqlalchemy import Column, Integer, Time, DateTime, ForeignKey, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.core.database import Base


class ShiftAssignment(Base):
    """
    Represents an employee's work shift on a specific day.
    Links employees to daily records with start and end times.

    Constraints:
    - One employee can only have one shift per day (unique_employee_per_day)
    - End time must be after start time (valid_time_range)
    """
    __tablename__ = "shift_assignments"

    id = Column(Integer, primary_key=True, index=True)
    daily_record_id = Column(
        Integer,
        ForeignKey("daily_records.id", ondelete="CASCADE"),
        nullable=False
    )
    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False
    )
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('daily_record_id', 'employee_id', name='unique_employee_per_day'),
        CheckConstraint('end_time > start_time', name='valid_time_range'),
        Index("idx_shift_assignments_daily_record", "daily_record_id"),
        Index("idx_shift_assignments_employee", "employee_id"),
    )

    # Relationships
    daily_record = relationship("DailyRecord", back_populates="shift_assignments")
    employee = relationship("Employee", back_populates="shift_assignments")

    @property
    def hours_worked(self) -> float:
        """
        Calculate hours worked from start and end time.
        Returns the duration in hours as a float.
        """
        start = datetime.combine(datetime.min, self.start_time)
        end = datetime.combine(datetime.min, self.end_time)
        delta = end - start
        return delta.total_seconds() / 3600
