from sqlalchemy import Column, Integer, Numeric, Text, DateTime, ForeignKey, Enum as SQLEnum, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class SpoilageReason(str, enum.Enum):
    EXPIRED = "expired"                    # Przeterminowany
    OVER_PREPARED = "over_prepared"        # Nadmiernie przygotowany
    CONTAMINATED = "contaminated"          # Zanieczyszczony
    EQUIPMENT_FAILURE = "equipment_failure"  # Awaria sprzetu
    OTHER = "other"                        # Inne


class Spoilage(Base):
    """
    Records spoiled ingredients with reason tracking.
    Spoilage is deducted from shop inventory for calculations.
    """
    __tablename__ = "spoilages"

    id = Column(Integer, primary_key=True, index=True)
    daily_record_id = Column(Integer, ForeignKey("daily_records.id", ondelete="CASCADE"), nullable=False, index=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Numeric(10, 3), nullable=False)  # In ingredient's unit (kg or count)
    reason = Column(
        SQLEnum(SpoilageReason, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    notes = Column(Text, nullable=True)  # Optional explanation
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_spoilage_quantity_positive"),
    )

    # Relationships
    daily_record = relationship("DailyRecord", back_populates="spoilages")
    ingredient = relationship("Ingredient", back_populates="spoilages")
