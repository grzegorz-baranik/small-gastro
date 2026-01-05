from sqlalchemy import Column, Integer, String, Numeric, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Position(Base):
    """
    Represents a job position (e.g., Cook, Cashier) with a default hourly rate.
    Employees are assigned to positions and inherit the rate unless overridden.
    """
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    hourly_rate = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    employees = relationship("Employee", back_populates="position")
