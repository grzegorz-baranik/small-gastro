from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class StorageTransfer(Base):
    """
    Records transfers of ingredients from storage to shop.
    Deducts from storage inventory and adds to shop inventory.
    """
    __tablename__ = "storage_transfers"

    id = Column(Integer, primary_key=True, index=True)
    daily_record_id = Column(Integer, ForeignKey("daily_records.id", ondelete="CASCADE"), nullable=False, index=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Numeric(10, 3), nullable=False)  # In ingredient's unit (kg or count)
    transferred_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_transfer_quantity_positive"),
    )

    # Relationships
    daily_record = relationship("DailyRecord", back_populates="storage_transfers")
    ingredient = relationship("Ingredient", back_populates="storage_transfers")
