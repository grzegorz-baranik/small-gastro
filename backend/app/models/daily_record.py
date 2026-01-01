from sqlalchemy import Column, Integer, String, Date, DateTime, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class DayStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"


class DailyRecord(Base):
    __tablename__ = "daily_records"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True)
    status = Column(SQLEnum(DayStatus), nullable=False, default=DayStatus.OPEN)
    opened_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    inventory_snapshots = relationship("InventorySnapshot", back_populates="daily_record", cascade="all, delete-orphan")
    sales_items = relationship("SalesItem", back_populates="daily_record", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="daily_record")
