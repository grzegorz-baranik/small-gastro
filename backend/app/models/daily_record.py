from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base, EnumColumn


class DayStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"


class DailyRecord(Base):
    __tablename__ = "daily_records"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True, index=True)  # Frequently filtered
    status = Column(EnumColumn(DayStatus), nullable=False, default=DayStatus.OPEN)

    # Financial summary fields
    total_income_pln = Column(Numeric(10, 2), nullable=True)  # Calculated from sales
    total_delivery_cost_pln = Column(Numeric(10, 2), nullable=False, server_default="0")
    total_spoilage_cost_pln = Column(Numeric(10, 2), nullable=False, server_default="0")

    # Revenue tracking for hybrid sales
    recorded_revenue_pln = Column(Numeric(10, 2), nullable=True)
    calculated_revenue_pln = Column(Numeric(10, 2), nullable=True)
    revenue_discrepancy_pln = Column(Numeric(10, 2), nullable=True)
    revenue_source = Column(String(20), server_default="calculated")  # 'recorded', 'calculated', 'hybrid'

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
    shift_assignments = relationship("ShiftAssignment", back_populates="daily_record", cascade="all, delete-orphan")
    batch_deductions = relationship("BatchDeduction", back_populates="daily_record")
    recorded_sales = relationship("RecordedSale", back_populates="daily_record", cascade="all, delete-orphan")
