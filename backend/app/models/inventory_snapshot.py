from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class SnapshotType(str, enum.Enum):
    OPEN = "open"
    CLOSE = "close"


class InventorySnapshot(Base):
    __tablename__ = "inventory_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    daily_record_id = Column(Integer, ForeignKey("daily_records.id", ondelete="CASCADE"), nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id", ondelete="RESTRICT"), nullable=False)
    snapshot_type = Column(SQLEnum(SnapshotType), nullable=False)
    quantity_grams = Column(Numeric(10, 2), nullable=True)  # for weight-based
    quantity_count = Column(Integer, nullable=True)          # for count-based
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("daily_record_id", "ingredient_id", "snapshot_type", name="uq_snapshot_per_day_ingredient_type"),
    )

    # Relationships
    daily_record = relationship("DailyRecord", back_populates="inventory_snapshots")
    ingredient = relationship("Ingredient", back_populates="inventory_snapshots")
