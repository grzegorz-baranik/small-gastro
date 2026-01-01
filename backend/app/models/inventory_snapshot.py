from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class SnapshotType(str, enum.Enum):
    OPEN = "open"
    CLOSE = "close"


class InventoryLocation(str, enum.Enum):
    SHOP = "shop"      # Shop floor inventory
    STORAGE = "storage"  # Storage room inventory


class InventorySnapshot(Base):
    """
    Records inventory counts at specific points in time (opening/closing).
    Supports both shop floor and storage locations.
    """
    __tablename__ = "inventory_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    daily_record_id = Column(Integer, ForeignKey("daily_records.id", ondelete="CASCADE"), nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id", ondelete="RESTRICT"), nullable=False)
    snapshot_type = Column(SQLEnum(SnapshotType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    location = Column(
        SQLEnum(InventoryLocation, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        server_default="shop"
    )
    quantity = Column(Numeric(10, 3), nullable=False)  # Unified quantity field (uses ingredient's unit)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "daily_record_id", "ingredient_id", "snapshot_type", "location",
            name="uq_snapshot_per_day_ingredient_type_location"
        ),
    )

    # Relationships
    daily_record = relationship("DailyRecord", back_populates="inventory_snapshots")
    ingredient = relationship("Ingredient", back_populates="inventory_snapshots")
