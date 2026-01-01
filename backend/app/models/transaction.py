from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Text, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class TransactionType(str, enum.Enum):
    EXPENSE = "expense"
    REVENUE = "revenue"


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(SQLEnum(TransactionType), nullable=False)
    category_id = Column(Integer, ForeignKey("expense_categories.id", ondelete="SET NULL"), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    description = Column(Text, nullable=True)
    transaction_date = Column(Date, nullable=False)
    daily_record_id = Column(Integer, ForeignKey("daily_records.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_transactions_date", "transaction_date"),
        Index("idx_transactions_type", "type"),
    )

    # Relationships
    category = relationship("ExpenseCategory", back_populates="transactions")
    daily_record = relationship("DailyRecord", back_populates="transactions")
