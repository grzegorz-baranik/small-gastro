from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from app.models.transaction import TransactionType, PaymentMethod, WagePeriodType


class TransactionBase(BaseModel):
    type: TransactionType
    category_id: Optional[int] = None
    amount: Decimal = Field(..., gt=0)
    payment_method: PaymentMethod
    description: Optional[str] = None
    transaction_date: date


class TransactionCreate(TransactionBase):
    daily_record_id: Optional[int] = None
    # Wage-specific fields (optional)
    employee_id: Optional[int] = None
    wage_period_type: Optional[WagePeriodType] = None
    wage_period_start: Optional[date] = None
    wage_period_end: Optional[date] = None


class TransactionUpdate(BaseModel):
    type: Optional[TransactionType] = None
    category_id: Optional[int] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    payment_method: Optional[PaymentMethod] = None
    description: Optional[str] = None
    transaction_date: Optional[date] = None
    # Wage-specific fields
    employee_id: Optional[int] = None
    wage_period_type: Optional[WagePeriodType] = None
    wage_period_start: Optional[date] = None
    wage_period_end: Optional[date] = None


class TransactionResponse(TransactionBase):
    id: int
    daily_record_id: Optional[int] = None
    category_name: Optional[str] = None
    created_at: datetime
    # Wage-specific fields
    employee_id: Optional[int] = None
    employee_name: Optional[str] = None
    wage_period_type: Optional[WagePeriodType] = None
    wage_period_start: Optional[date] = None
    wage_period_end: Optional[date] = None

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    total: int


class TransactionSummary(BaseModel):
    period_start: date
    period_end: date
    total_revenue: Decimal
    total_expenses: Decimal
    net_profit: Decimal
    revenue_by_payment: dict[str, Decimal]
    expenses_by_category: dict[str, Decimal]
