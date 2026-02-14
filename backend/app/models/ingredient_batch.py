from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean, Date, DateTime, Text,
    ForeignKey, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base, EnumColumn


class BatchLocation(str, enum.Enum):
    """Location where the batch is stored."""
    STORAGE = "storage"  # In storage/warehouse
    SHOP = "shop"        # In shop/prep area


class IngredientBatch(Base):
    """
    Tracks batches of ingredients with expiry dates and FIFO tracking.

    Batch numbers are auto-generated in format: B-YYYYMMDD-NNN
    where NNN is a sequential number for that day.

    Batches can be linked to delivery items for traceability.
    Expiry alerts are triggered 7 days before expiration.
    """
    __tablename__ = "ingredient_batches"

    id = Column(Integer, primary_key=True, index=True)
    batch_number = Column(String(20), nullable=False, unique=True, index=True)
    ingredient_id = Column(
        Integer,
        ForeignKey("ingredients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    delivery_item_id = Column(
        Integer,
        ForeignKey("delivery_items.id", ondelete="SET NULL"),
        nullable=True
    )
    expiry_date = Column(Date, nullable=True, index=True)
    initial_quantity = Column(Numeric(10, 3), nullable=False)
    remaining_quantity = Column(Numeric(10, 3), nullable=False)
    location = Column(String(20), nullable=False, server_default="storage")
    is_active = Column(Boolean, nullable=False, server_default="true")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("initial_quantity > 0", name="check_batch_initial_quantity_positive"),
        CheckConstraint("remaining_quantity >= 0", name="check_batch_remaining_quantity_non_negative"),
        CheckConstraint("location IN ('storage', 'shop')", name="check_batch_location_valid"),
    )

    # Relationships
    ingredient = relationship("Ingredient", back_populates="batches")
    delivery_item = relationship("DeliveryItem", back_populates="batch", uselist=False)
    deductions = relationship("BatchDeduction", back_populates="batch", cascade="all, delete-orphan")
    spoilages = relationship("Spoilage", back_populates="batch")


class BatchDeduction(Base):
    """
    Audit trail for batch quantity deductions.

    Records when and why quantity was deducted from a batch:
    - sales: Product sold consuming ingredients
    - spoilage: Ingredient spoiled/wasted
    - transfer: Moved between locations
    - adjustment: Manual inventory adjustment

    reference_type and reference_id link to the source record.
    """
    __tablename__ = "batch_deductions"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(
        Integer,
        ForeignKey("ingredient_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    daily_record_id = Column(
        Integer,
        ForeignKey("daily_records.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    quantity = Column(Numeric(10, 3), nullable=False)
    reason = Column(String(50), nullable=False)  # sales, spoilage, transfer, adjustment
    reference_type = Column(String(50), nullable=True)  # Type of related record (e.g., 'spoilage')
    reference_id = Column(Integer, nullable=True)  # ID of related record
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_batch_deduction_quantity_positive"),
    )

    # Relationships
    batch = relationship("IngredientBatch", back_populates="deductions")
    daily_record = relationship("DailyRecord", back_populates="batch_deductions")
