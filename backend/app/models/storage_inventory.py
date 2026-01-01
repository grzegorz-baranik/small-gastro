from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class StorageInventory(Base):
    """
    Tracks current storage room inventory for each ingredient.
    Updated during weekly storage counts and when transfers occur.
    Each ingredient has at most one storage inventory record.
    """
    __tablename__ = "storage_inventory"

    id = Column(Integer, primary_key=True, index=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id", ondelete="RESTRICT"), nullable=False, unique=True)
    quantity = Column(Numeric(10, 3), nullable=False, server_default="0")  # In ingredient's unit
    last_counted_at = Column(DateTime(timezone=True), nullable=True)  # Last manual count
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("quantity >= 0", name="check_storage_quantity_non_negative"),
    )

    # Relationships
    ingredient = relationship("Ingredient", back_populates="storage_inventory")
