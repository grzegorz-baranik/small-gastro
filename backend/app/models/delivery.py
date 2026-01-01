from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Delivery(Base):
    """
    Records ingredient deliveries to the shop.
    Deliveries add to shop inventory and track costs.
    """
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)
    daily_record_id = Column(Integer, ForeignKey("daily_records.id", ondelete="CASCADE"), nullable=False, index=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Numeric(10, 3), nullable=False)  # In ingredient's unit (kg or count)
    price_pln = Column(Numeric(10, 2), nullable=False)  # Cost of delivery
    delivered_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_delivery_quantity_positive"),
        CheckConstraint("price_pln >= 0", name="check_delivery_price_non_negative"),
    )

    # Relationships
    daily_record = relationship("DailyRecord", back_populates="deliveries")
    ingredient = relationship("Ingredient", back_populates="deliveries")
