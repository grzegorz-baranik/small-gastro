from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base, EnumColumn


class TransactionType(str, enum.Enum):
    EXPENSE = "expense"
    REVENUE = "revenue"


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"


class WagePeriodType(str, enum.Enum):
    """Period type for wage transactions."""
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(EnumColumn(TransactionType), nullable=False)
    category_id = Column(Integer, ForeignKey("expense_categories.id", ondelete="SET NULL"), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(EnumColumn(PaymentMethod), nullable=False)
    description = Column(Text, nullable=True)
    transaction_date = Column(Date, nullable=False)
    daily_record_id = Column(Integer, ForeignKey("daily_records.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Wage-specific fields (nullable, only used for wage transactions)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    wage_period_type = Column(EnumColumn(WagePeriodType), nullable=True)
    wage_period_start = Column(Date, nullable=True)
    wage_period_end = Column(Date, nullable=True)

    __table_args__ = (
        Index("idx_transactions_date", "transaction_date"),
        Index("idx_transactions_type", "type"),
        Index("idx_transactions_employee", "employee_id"),
    )

    # Relationships
    category = relationship("ExpenseCategory", back_populates="transactions")
    daily_record = relationship("DailyRecord", back_populates="transactions")
    employee = relationship("Employee", back_populates="transactions")
    delivery = relationship("Delivery", back_populates="transaction", uselist=False)
