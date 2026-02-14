from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, ForeignKey,
    CheckConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal
import enum
from app.core.database import Base, EnumColumn


class VoidReason(str, enum.Enum):
    """Reasons for voiding a recorded sale."""
    CUSTOMER_REFUND = "customer_refund"
    ENTRY_ERROR = "entry_error"
    DUPLICATE = "duplicate"
    TEST_ENTRY = "test_entry"
    OTHER = "other"


class RecordedSale(Base):
    """
    Records manually entered sales during daily operations.
    Runs parallel to CalculatedSale for reconciliation between
    recorded sales (what was entered) and calculated sales (derived from inventory).

    Supports soft-delete through voided_at timestamp rather than hard deletes,
    preserving audit trail for reconciliation purposes.
    """
    __tablename__ = "recorded_sales"

    id = Column(Integer, primary_key=True, index=True)
    daily_record_id = Column(
        Integer,
        ForeignKey("daily_records.id", ondelete="CASCADE"),
        nullable=False
    )
    product_variant_id = Column(
        Integer,
        ForeignKey("product_variants.id", ondelete="RESTRICT"),
        nullable=False
    )
    shift_assignment_id = Column(
        Integer,
        ForeignKey("shift_assignments.id", ondelete="SET NULL"),
        nullable=True
    )
    quantity = Column(Integer, nullable=False, default=1)
    unit_price_pln = Column(Numeric(10, 2), nullable=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Soft delete fields
    voided_at = Column(DateTime(timezone=True), nullable=True)
    void_reason = Column(EnumColumn(VoidReason), nullable=True)
    void_notes = Column(String(255), nullable=True)

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_recorded_sale_quantity_positive"),
        CheckConstraint("unit_price_pln > 0", name="check_recorded_sale_price_positive"),
        Index("idx_recorded_sales_daily_record", "daily_record_id"),
        Index("idx_recorded_sales_variant", "product_variant_id"),
        Index("idx_recorded_sales_recorded_at", "recorded_at"),
    )

    # Relationships
    daily_record = relationship("DailyRecord", back_populates="recorded_sales")
    product_variant = relationship("ProductVariant", back_populates="recorded_sales")
    shift_assignment = relationship("ShiftAssignment", back_populates="recorded_sales")

    @property
    def is_voided(self) -> bool:
        """Check if this sale has been voided."""
        return self.voided_at is not None

    @property
    def total_pln(self) -> Decimal:
        """Calculate total value of this sale (quantity * unit_price)."""
        return Decimal(self.quantity) * self.unit_price_pln
