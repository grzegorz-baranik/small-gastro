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


def _to_response(t: Transaction) -> TransactionResponse:
    """Convert Transaction model to TransactionResponse schema."""
    return TransactionResponse(
        id=t.id,
        type=t.type,
        category_id=t.category_id,
        amount=t.amount,
        payment_method=t.payment_method,
        description=t.description,
        transaction_date=t.transaction_date,
        daily_record_id=t.daily_record_id,
        category_name=t.category.name if t.category_id and t.category else None,
        created_at=t.created_at,
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
    db: Session = Depends(get_db),
):
    """Pobierz liste transakcji z filtrami."""
    items, total = transaction_service.get_transactions(
        db, skip, limit, type_filter, category_id, payment_method, date_from, date_to
    )
    return TransactionListResponse(items=[_to_response(t) for t in items], total=total)


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
