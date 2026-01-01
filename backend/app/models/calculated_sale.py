from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class CalculatedSale(Base):
    """
    Records derived sales calculated from ingredient usage.
    Sales are derived by dividing ingredient usage by recipe amounts.
    """
    __tablename__ = "calculated_sales"

    id = Column(Integer, primary_key=True, index=True)
    daily_record_id = Column(Integer, ForeignKey("daily_records.id", ondelete="CASCADE"), nullable=False)
    product_variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=False)
    quantity_sold = Column(Numeric(10, 2), nullable=False)  # Derived quantity (rounded up)
    revenue_pln = Column(Numeric(10, 2), nullable=False)  # quantity_sold * price_pln
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("quantity_sold >= 0", name="check_calc_sale_quantity_non_negative"),
        CheckConstraint("revenue_pln >= 0", name="check_calc_sale_revenue_non_negative"),
    )

    # Relationships
    daily_record = relationship("DailyRecord", back_populates="calculated_sales")
    product_variant = relationship("ProductVariant", back_populates="calculated_sales")
