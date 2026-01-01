from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class ExpenseCategory(Base):
    __tablename__ = "expense_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    parent_id = Column(Integer, ForeignKey("expense_categories.id", ondelete="RESTRICT"), nullable=True)
    level = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        CheckConstraint("level >= 1 AND level <= 3", name="check_level_range"),
    )

    # Relationships
    parent = relationship("ExpenseCategory", remote_side=[id], back_populates="children")
    children = relationship("ExpenseCategory", back_populates="parent")
    transactions = relationship("Transaction", back_populates="category")
