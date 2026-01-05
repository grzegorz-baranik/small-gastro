from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from app.api.deps import get_db
from app.core.i18n import t
from app.models.transaction import Transaction, TransactionType, PaymentMethod
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionListResponse,
    TransactionSummary,
)
from app.services import transaction_service
from app.services.transaction_service import InvalidCategoryError

router = APIRouter()


def _to_response(txn: Transaction) -> TransactionResponse:
    """Convert Transaction model to TransactionResponse schema."""
    return TransactionResponse(
        id=txn.id,
        type=txn.type,
        category_id=txn.category_id,
        amount=txn.amount,
        payment_method=txn.payment_method,
        description=txn.description,
        transaction_date=txn.transaction_date,
        daily_record_id=txn.daily_record_id,
        category_name=txn.category.name if txn.category_id and txn.category else None,
        created_at=txn.created_at,
        # Wage-specific fields
        employee_id=txn.employee_id,
        employee_name=txn.employee.name if txn.employee_id and txn.employee else None,
        wage_period_type=txn.wage_period_type,
        wage_period_start=txn.wage_period_start,
        wage_period_end=txn.wage_period_end,
    )


@router.get("", response_model=TransactionListResponse)
def list_transactions(
    skip: int = 0,
    limit: int = 100,
    type_filter: Optional[TransactionType] = None,
    category_id: Optional[int] = None,
    payment_method: Optional[PaymentMethod] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    employee_id: Optional[int] = Query(None, description="Filtruj po pracowniku"),
    db: Session = Depends(get_db),
):
    """Pobierz liste transakcji z filtrami."""
    items, total = transaction_service.get_transactions(
        db, skip, limit, type_filter, category_id, payment_method, date_from, date_to, employee_id
    )
    return TransactionListResponse(items=[_to_response(txn) for txn in items], total=total)


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    data: TransactionCreate,
    db: Session = Depends(get_db),
):
    """Utworz nowa transakcje."""
    try:
        transaction = transaction_service.create_transaction(db, data)
    except InvalidCategoryError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return _to_response(transaction)


@router.get("/summary", response_model=TransactionSummary)
def get_transaction_summary(
    date_from: date = Query(...),
    date_to: date = Query(...),
    db: Session = Depends(get_db),
):
    """Pobierz podsumowanie transakcji za okres."""
    return transaction_service.get_transaction_summary(db, date_from, date_to)


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
):
    """Pobierz transakcje po ID."""
    transaction = transaction_service.get_transaction(db, transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.transaction_not_found"),
        )
    return _to_response(transaction)


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    data: TransactionUpdate,
    db: Session = Depends(get_db),
):
    """Zaktualizuj transakcje."""
    try:
        transaction = transaction_service.update_transaction(db, transaction_id, data)
    except InvalidCategoryError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.transaction_not_found"),
        )
    return _to_response(transaction)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
):
    """Usun transakcje."""
    result = transaction_service.delete_transaction(db, transaction_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.transaction_not_found"),
        )
