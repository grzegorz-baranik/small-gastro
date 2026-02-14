from sqlalchemy import Column, Integer, Time, DateTime, ForeignKey, UniqueConstraint, CheckConstraint, Index, SmallInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.core.database import Base


class ShiftTemplate(Base):
    """
    Represents a recurring shift pattern for an employee.

    A shift template defines when an employee is scheduled to work on a given day of the week.
    For example: "Anna works Mon-Fri 08:00-16:00" would be 5 separate templates.

    Constraints:
    - One employee can only have one template per day of week (unique_template_per_day)
    - Day of week must be 0-6 (Monday=0, Sunday=6)
    - End time must be after start time (valid_time_range)
    """
    __tablename__ = "shift_templates"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(
        Integer,
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False
    )
    day_of_week = Column(SmallInteger, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('employee_id', 'day_of_week', name='unique_template_per_day'),
        CheckConstraint('day_of_week >= 0 AND day_of_week <= 6', name='valid_day_of_week'),
        CheckConstraint('end_time > start_time', name='template_valid_time_range'),
        Index("idx_shift_templates_employee", "employee_id"),
        Index("idx_shift_templates_day", "day_of_week"),
    )

    # Relationships
    employee = relationship("Employee", back_populates="shift_templates")

    @property
    def hours(self) -> float:
        """
        Calculate shift duration in hours.
        Returns the duration as a float.
        """
        start = datetime.combine(datetime.min, self.start_time)
        end = datetime.combine(datetime.min, self.end_time)
        delta = end - start
        return delta.total_seconds() / 3600
