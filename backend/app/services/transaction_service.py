from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
from typing import Optional, Union
from datetime import date
from decimal import Decimal
from app.models.transaction import Transaction, TransactionType, PaymentMethod
from app.models.expense_category import ExpenseCategory
from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionSummary
from app.core.i18n import t


# Use constant from model for single source of truth
LEAF_CATEGORY_LEVEL = ExpenseCategory.LEAF_LEVEL


class InvalidCategoryError(Exception):
    """Raised when a non-leaf category is assigned to a transaction."""
    pass


def validate_leaf_category(db: Session, category_id: Optional[int]) -> None:
    """Validate that the category is a leaf category (level 3) if provided."""
    if category_id is None:
        return

    category = db.query(ExpenseCategory).filter(ExpenseCategory.id == category_id).first()
    if not category:
        raise InvalidCategoryError(t("errors.category_not_exists"))
    if category.level != LEAF_CATEGORY_LEVEL:
        raise InvalidCategoryError(
            t("errors.category_not_leaf", name=category.name, level=category.level)
        )


def _normalize_type_filter(
    type_filter: Optional[Union[TransactionType, str]]
) -> Optional[TransactionType]:
    """Convert string type_filter to TransactionType enum if needed."""
    if type_filter is None:
        return None
    if isinstance(type_filter, TransactionType):
        return type_filter
    # Handle string values
    try:
        return TransactionType(type_filter)
    except ValueError:
        # Try uppercase conversion for case-insensitive matching
        try:
            return TransactionType(type_filter.lower())
        except ValueError:
            return None


def get_transactions(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    type_filter: Optional[Union[TransactionType, str]] = None,
    category_id: Optional[int] = None,
    payment_method: Optional[PaymentMethod] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> tuple[list[Transaction], int]:
    # Eagerly load the category relationship to avoid N+1 queries
    # and ensure the relationship is available after the query
    query = db.query(Transaction).options(joinedload(Transaction.category))

    # Normalize type_filter to handle both enum and string values
    normalized_type = _normalize_type_filter(type_filter)
    if normalized_type is not None:
        query = query.filter(Transaction.type == normalized_type)
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    if payment_method:
        query = query.filter(Transaction.payment_method == payment_method)
    if date_from:
        query = query.filter(Transaction.transaction_date >= date_from)
    if date_to:
        query = query.filter(Transaction.transaction_date <= date_to)

    # Count without the joinedload for efficiency
    count_query = db.query(Transaction)
    if normalized_type is not None:
        count_query = count_query.filter(Transaction.type == normalized_type)
    if category_id:
        count_query = count_query.filter(Transaction.category_id == category_id)
    if payment_method:
        count_query = count_query.filter(Transaction.payment_method == payment_method)
    if date_from:
        count_query = count_query.filter(Transaction.transaction_date >= date_from)
    if date_to:
        count_query = count_query.filter(Transaction.transaction_date <= date_to)
    total = count_query.count()

    items = query.order_by(Transaction.transaction_date.desc(), Transaction.id.desc()).offset(skip).limit(limit).all()

    return items, total


def get_transaction(db: Session, transaction_id: int) -> Optional[Transaction]:
    return (
        db.query(Transaction)
        .options(joinedload(Transaction.category))
        .filter(Transaction.id == transaction_id)
        .first()
    )


def create_transaction(db: Session, data: TransactionCreate) -> Transaction:
    # Validate that only leaf categories can be assigned
    if data.type == TransactionType.EXPENSE:
        validate_leaf_category(db, data.category_id)

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

    # Re-fetch with eager loading to ensure category relationship is loaded
    return get_transaction(db, db_transaction.id)


def update_transaction(db: Session, transaction_id: int, data: TransactionUpdate) -> Optional[Transaction]:
    db_transaction = get_transaction(db, transaction_id)
    if not db_transaction:
        return None

    # Validate category if being updated on an expense transaction
    update_data = data.model_dump(exclude_unset=True)
    if "category_id" in update_data and db_transaction.type == TransactionType.EXPENSE:
        validate_leaf_category(db, update_data["category_id"])

    for field, value in update_data.items():
        setattr(db_transaction, field, value)

    db.commit()

    # Re-fetch with eager loading to ensure category relationship is loaded
    return get_transaction(db, transaction_id)


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
        expenses_by_category[t("labels.uncategorized")] = Decimal(str(uncategorized))

    return TransactionSummary(
        period_start=date_from,
        period_end=date_to,
        total_revenue=Decimal(str(revenue)),
        total_expenses=Decimal(str(expenses)),
        net_profit=Decimal(str(revenue)) - Decimal(str(expenses)),
        revenue_by_payment=revenue_by_payment,
        expenses_by_category=expenses_by_category,
    )
