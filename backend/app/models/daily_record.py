from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Text, Enum as SQLEnum, Index
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
    date = Column(Date, nullable=False, unique=True, index=True)  # Frequently filtered
    status = Column(SQLEnum(DayStatus), nullable=False, default=DayStatus.OPEN)

    # Financial summary fields
    total_income_pln = Column(Numeric(10, 2), nullable=True)  # Calculated from sales
    total_delivery_cost_pln = Column(Numeric(10, 2), nullable=False, server_default="0")
    total_spoilage_cost_pln = Column(Numeric(10, 2), nullable=False, server_default="0")

    # Timestamps
    opened_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    inventory_snapshots = relationship("InventorySnapshot", back_populates="daily_record", cascade="all, delete-orphan")
    sales_items = relationship("SalesItem", back_populates="daily_record", cascade="all, delete-orphan")  # Legacy
    transactions = relationship("Transaction", back_populates="daily_record")
    deliveries = relationship("Delivery", back_populates="daily_record", cascade="all, delete-orphan")
    storage_transfers = relationship("StorageTransfer", back_populates="daily_record", cascade="all, delete-orphan")
    spoilages = relationship("Spoilage", back_populates="daily_record", cascade="all, delete-orphan")
    calculated_sales = relationship("CalculatedSale", back_populates="daily_record", cascade="all, delete-orphan")
