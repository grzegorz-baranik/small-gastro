from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from decimal import Decimal
from app.models.transaction import Transaction, TransactionType, PaymentMethod
from app.models.sales_item import SalesItem
from app.models.daily_record import DailyRecord, DayStatus
from app.models.expense_category import ExpenseCategory
from app.schemas.dashboard import (
    DashboardOverview,
    IncomeBreakdown,
    ExpensesBreakdown,
    ProfitData,
    DiscrepancyWarning,
)
from app.services import inventory_service


DISCREPANCY_THRESHOLD_LOW = 5  # 5%
DISCREPANCY_THRESHOLD_MEDIUM = 10  # 10%
DISCREPANCY_THRESHOLD_HIGH = 20  # 20%


def _get_period_dates(period: str) -> tuple[date, date]:
    today = date.today()
    if period == "today":
        return today, today
    elif period == "week":
        start = today - timedelta(days=today.weekday())
        return start, today
    elif period == "month":
        start = today.replace(day=1)
        return start, today
    return today, today


def _calculate_income(db: Session, date_from: date, date_to: date) -> Decimal:
    # Sales income
    sales_result = db.query(func.sum(SalesItem.total_price)).join(
        DailyRecord
    ).filter(
        DailyRecord.date >= date_from,
        DailyRecord.date <= date_to,
    ).scalar()
    sales = Decimal(str(sales_result)) if sales_result is not None else Decimal("0")

    # Revenue transactions
    revenue_result = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == TransactionType.REVENUE,
        Transaction.transaction_date >= date_from,
        Transaction.transaction_date <= date_to,
    ).scalar()
    revenue = Decimal(str(revenue_result)) if revenue_result is not None else Decimal("0")

    return sales + revenue


def _calculate_expenses(db: Session, date_from: date, date_to: date) -> Decimal:
    expenses_result = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == TransactionType.EXPENSE,
        Transaction.transaction_date >= date_from,
        Transaction.transaction_date <= date_to,
    ).scalar()

    return Decimal(str(expenses_result)) if expenses_result is not None else Decimal("0")


def get_dashboard_overview(db: Session) -> DashboardOverview:
    today = date.today()

    # Today
    today_revenue = _calculate_income(db, today, today)
    today_expenses = _calculate_expenses(db, today, today)
    today_profit = today_revenue - today_expenses

    # This week
    week_start = today - timedelta(days=today.weekday())
    week_revenue = _calculate_income(db, week_start, today)
    week_expenses = _calculate_expenses(db, week_start, today)
    week_profit = week_revenue - week_expenses

    # This month
    month_start = today.replace(day=1)
    month_revenue = _calculate_income(db, month_start, today)
    month_expenses = _calculate_expenses(db, month_start, today)
    month_profit = month_revenue - month_expenses

    # Check if day is open
    today_record = db.query(DailyRecord).filter(DailyRecord.date == today).first()
    day_is_open = today_record is not None and today_record.status == DayStatus.OPEN

    # Count active warnings
    warnings = get_discrepancy_warnings(db, days_back=7)
    active_warnings = len([w for w in warnings if w.severity in ["medium", "high"]])

    return DashboardOverview(
        today_revenue=today_revenue,
        today_expenses=today_expenses,
        today_profit=today_profit,
        week_revenue=week_revenue,
        week_expenses=week_expenses,
        week_profit=week_profit,
        month_revenue=month_revenue,
        month_expenses=month_expenses,
        month_profit=month_profit,
        day_is_open=day_is_open,
        active_warnings=active_warnings,
    )


def get_income_breakdown(db: Session, period: str) -> IncomeBreakdown:
    date_from, date_to = _get_period_dates(period)

    total = _calculate_income(db, date_from, date_to)

    # By payment method
    by_payment = {}
    for method in PaymentMethod:
        amount_result = db.query(func.sum(Transaction.amount)).filter(
            Transaction.type == TransactionType.REVENUE,
            Transaction.payment_method == method,
            Transaction.transaction_date >= date_from,
            Transaction.transaction_date <= date_to,
        ).scalar()
        if amount_result is not None and amount_result > 0:
            by_payment[method.value] = Decimal(str(amount_result))

    # Add sales (assuming cash for simplicity, could be tracked separately)
    sales_result = db.query(func.sum(SalesItem.total_price)).join(
        DailyRecord
    ).filter(
        DailyRecord.date >= date_from,
        DailyRecord.date <= date_to,
    ).scalar()

    if sales_result is not None and sales_result > 0:
        by_payment["sprzedaz"] = Decimal(str(sales_result))

    return IncomeBreakdown(
        period=period,
        total=total,
        by_payment_method=by_payment,
    )


def get_expenses_breakdown(db: Session, period: str) -> ExpensesBreakdown:
    date_from, date_to = _get_period_dates(period)

    total = _calculate_expenses(db, date_from, date_to)

    # By category
    by_category = {}
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
        if amount is not None:
            by_category[cat_name] = Decimal(str(amount))

    # Uncategorized
    uncategorized_result = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == TransactionType.EXPENSE,
        Transaction.category_id == None,
        Transaction.transaction_date >= date_from,
        Transaction.transaction_date <= date_to,
    ).scalar()

    if uncategorized_result is not None and uncategorized_result > 0:
        by_category["Bez kategorii"] = Decimal(str(uncategorized_result))

    return ExpensesBreakdown(
        period=period,
        total=total,
        by_category=by_category,
    )


def get_profit_data(db: Session, period: str) -> ProfitData:
    date_from, date_to = _get_period_dates(period)

    revenue = _calculate_income(db, date_from, date_to)
    expenses = _calculate_expenses(db, date_from, date_to)
    profit = revenue - expenses

    margin = None
    if revenue > 0:
        margin = (profit / revenue) * 100

    return ProfitData(
        period=period,
        revenue=revenue,
        expenses=expenses,
        profit=profit,
        margin_percent=margin,
    )


def get_discrepancy_warnings(db: Session, days_back: int = 7) -> list[DiscrepancyWarning]:
    warnings = []
    today = date.today()
    start_date = today - timedelta(days=days_back)

    # Get closed daily records
    records = db.query(DailyRecord).filter(
        DailyRecord.status == DayStatus.CLOSED,
        DailyRecord.date >= start_date,
        DailyRecord.date <= today,
    ).all()

    warning_id = 0
    for record in records:
        try:
            discrepancies = inventory_service.calculate_discrepancies(db, record.id)
        except Exception:
            # Skip records that fail discrepancy calculation
            continue

        for disc in discrepancies:
            if disc.discrepancy_percent is None:
                continue

            abs_percent = abs(disc.discrepancy_percent)

            if abs_percent < DISCREPANCY_THRESHOLD_LOW:
                continue

            if abs_percent >= DISCREPANCY_THRESHOLD_HIGH:
                severity = "high"
            elif abs_percent >= DISCREPANCY_THRESHOLD_MEDIUM:
                severity = "medium"
            else:
                severity = "low"

            warning_id += 1
            warnings.append(DiscrepancyWarning(
                id=warning_id,
                date=record.date,
                ingredient_id=disc.ingredient_id,
                ingredient_name=disc.ingredient_name,
                expected_used=disc.expected_used,
                actual_used=disc.actual_used,
                discrepancy=disc.discrepancy,
                discrepancy_percent=disc.discrepancy_percent,
                severity=severity,
            ))

    # Sort by severity (high first), then by discrepancy percentage (highest first)
    severity_order = {"high": 0, "medium": 1, "low": 2}
    warnings.sort(key=lambda w: (severity_order.get(w.severity, 3), -abs(w.discrepancy_percent)))

    return warnings
