from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional
from datetime import date
from decimal import Decimal
from app.models.transaction import Transaction, TransactionType, PaymentMethod
from app.models.expense_category import ExpenseCategory
from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionSummary


def get_transactions(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    type_filter: Optional[TransactionType] = None,
    category_id: Optional[int] = None,
    payment_method: Optional[PaymentMethod] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> tuple[list[Transaction], int]:
    query = db.query(Transaction)

    if type_filter:
        query = query.filter(Transaction.type == type_filter)
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    if payment_method:
        query = query.filter(Transaction.payment_method == payment_method)
    if date_from:
        query = query.filter(Transaction.transaction_date >= date_from)
    if date_to:
        query = query.filter(Transaction.transaction_date <= date_to)

    total = query.count()
    items = query.order_by(Transaction.transaction_date.desc(), Transaction.id.desc()).offset(skip).limit(limit).all()

    return items, total


def get_transaction(db: Session, transaction_id: int) -> Optional[Transaction]:
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()


def create_transaction(db: Session, data: TransactionCreate) -> Transaction:
    db_transaction = Transaction(
        type=data.type,
        category_id=data.category_id,
        amount=data.amount,
        payment_method=data.payment_method,
        description=data.description,
        transaction_date=data.transaction_date,
        daily_record_id=data.daily_record_id,
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def update_transaction(db: Session, transaction_id: int, data: TransactionUpdate) -> Optional[Transaction]:
    db_transaction = get_transaction(db, transaction_id)
    if not db_transaction:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_transaction, field, value)

    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def delete_transaction(db: Session, transaction_id: int) -> bool:
    db_transaction = get_transaction(db, transaction_id)
    if not db_transaction:
        return False

    db.delete(db_transaction)
    db.commit()
    return True


def get_transaction_summary(db: Session, date_from: date, date_to: date) -> TransactionSummary:
    # Total revenue
    revenue = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == TransactionType.REVENUE,
        Transaction.transaction_date >= date_from,
        Transaction.transaction_date <= date_to,
    ).scalar() or Decimal("0")

    # Total expenses
    expenses = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == TransactionType.EXPENSE,
        Transaction.transaction_date >= date_from,
        Transaction.transaction_date <= date_to,
    ).scalar() or Decimal("0")

    # Revenue by payment method
    revenue_by_payment = {}
    for method in PaymentMethod:
        amount = db.query(func.sum(Transaction.amount)).filter(
            Transaction.type == TransactionType.REVENUE,
            Transaction.payment_method == method,
            Transaction.transaction_date >= date_from,
            Transaction.transaction_date <= date_to,
        ).scalar() or Decimal("0")
        if amount > 0:
            revenue_by_payment[method.value] = Decimal(str(amount))

    # Expenses by category
    expenses_by_category = {}
    category_expenses = db.query(
        ExpenseCategory.name,
        func.sum(Transaction.amount)
    ).join(
        ExpenseCategory, Transaction.category_id == ExpenseCategory.id
    ).filter(
        Transaction.type == TransactionType.EXPENSE,
        Transaction.transaction_date >= date_from,
        Transaction.transaction_date <= date_to,
    ).group_by(ExpenseCategory.name).all()

    for cat_name, amount in category_expenses:
        expenses_by_category[cat_name] = Decimal(str(amount))

    # Uncategorized expenses
    uncategorized = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == TransactionType.EXPENSE,
        Transaction.category_id == None,
        Transaction.transaction_date >= date_from,
        Transaction.transaction_date <= date_to,
    ).scalar() or Decimal("0")
    if uncategorized > 0:
        expenses_by_category["Bez kategorii"] = Decimal(str(uncategorized))

    return TransactionSummary(
        period_start=date_from,
        period_end=date_to,
        total_revenue=Decimal(str(revenue)),
        total_expenses=Decimal(str(expenses)),
        net_profit=Decimal(str(revenue)) - Decimal(str(expenses)),
        revenue_by_payment=revenue_by_payment,
        expenses_by_category=expenses_by_category,
    )
