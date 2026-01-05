from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal
from app.core.database import Base


class Employee(Base):
    """
    Represents an employee who can be assigned to shifts.
    Each employee belongs to a position and can have an optional hourly rate override.
    """
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)
    hourly_rate_override = Column(Numeric(10, 2), nullable=True)  # NULL means use position's rate
    is_active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_employees_position", "position_id"),
        Index("idx_employees_active", "is_active"),
    )

    # Relationships
    position = relationship("Position", back_populates="employees")
    shift_assignments = relationship("ShiftAssignment", back_populates="employee")
    transactions = relationship("Transaction", back_populates="employee")

    @property
    def effective_hourly_rate(self) -> Decimal:
        """
        Return the effective hourly rate for this employee.
        Uses the override rate if set, otherwise falls back to position's default rate.
        """
        if self.hourly_rate_override is not None:
            return self.hourly_rate_override
        return self.position.hourly_rate
