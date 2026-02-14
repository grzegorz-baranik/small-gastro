from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, CheckConstraint, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Delivery(Base):
    """
    Records a delivery from a supplier.
    A delivery can contain multiple items (ingredients) and creates an expense transaction.
    """
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)
    daily_record_id = Column(Integer, ForeignKey("daily_records.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=True)
    invoice_number = Column(String(100), nullable=True)
    total_cost_pln = Column(Numeric(10, 2), nullable=False)  # Total cost of entire delivery
    notes = Column(Text, nullable=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True)
    delivered_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("total_cost_pln >= 0", name="check_delivery_total_cost_non_negative"),
    )

    # Relationships
    daily_record = relationship("DailyRecord", back_populates="deliveries")
    items = relationship("DeliveryItem", back_populates="delivery", cascade="all, delete-orphan")
    transaction = relationship("Transaction", back_populates="delivery")


class DeliveryItem(Base):
    """
    Individual ingredient line within a delivery.
    """
    __tablename__ = "delivery_items"

    id = Column(Integer, primary_key=True, index=True)
    delivery_id = Column(Integer, ForeignKey("deliveries.id", ondelete="CASCADE"), nullable=False, index=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Numeric(10, 3), nullable=False)  # In ingredient's unit (kg or count)
    cost_pln = Column(Numeric(10, 2), nullable=True)  # Optional per-item cost
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_delivery_item_quantity_positive"),
        CheckConstraint("cost_pln IS NULL OR cost_pln >= 0", name="check_delivery_item_cost_non_negative"),
    )

    # Relationships
    delivery = relationship("Delivery", back_populates="items")
    ingredient = relationship("Ingredient", back_populates="delivery_items")
