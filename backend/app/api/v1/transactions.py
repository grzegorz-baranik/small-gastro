from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from app.api.deps import get_db
from app.models.transaction import TransactionType, PaymentMethod
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionListResponse,
    TransactionSummary,
)
from app.services import transaction_service

router = APIRouter()


@router.get("/", response_model=TransactionListResponse)
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

    response_items = [
        TransactionResponse(
            id=t.id,
            type=t.type,
            category_id=t.category_id,
            amount=t.amount,
            payment_method=t.payment_method,
            description=t.description,
            transaction_date=t.transaction_date,
            daily_record_id=t.daily_record_id,
            category_name=t.category.name if t.category else None,
            created_at=t.created_at,
        )
        for t in items
    ]

    return TransactionListResponse(items=response_items, total=total)


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    data: TransactionCreate,
    db: Session = Depends(get_db),
):
    """Utworz nowa transakcje."""
    transaction = transaction_service.create_transaction(db, data)
    return TransactionResponse(
        id=transaction.id,
        type=transaction.type,
        category_id=transaction.category_id,
        amount=transaction.amount,
        payment_method=transaction.payment_method,
        description=transaction.description,
        transaction_date=transaction.transaction_date,
        daily_record_id=transaction.daily_record_id,
        category_name=transaction.category.name if transaction.category else None,
        created_at=transaction.created_at,
    )


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
            detail="Transakcja nie znaleziona",
        )
    return TransactionResponse(
        id=transaction.id,
        type=transaction.type,
        category_id=transaction.category_id,
        amount=transaction.amount,
        payment_method=transaction.payment_method,
        description=transaction.description,
        transaction_date=transaction.transaction_date,
        daily_record_id=transaction.daily_record_id,
        category_name=transaction.category.name if transaction.category else None,
        created_at=transaction.created_at,
    )


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    data: TransactionUpdate,
    db: Session = Depends(get_db),
):
    """Zaktualizuj transakcje."""
    transaction = transaction_service.update_transaction(db, transaction_id, data)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transakcja nie znaleziona",
        )
    return TransactionResponse(
        id=transaction.id,
        type=transaction.type,
        category_id=transaction.category_id,
        amount=transaction.amount,
        payment_method=transaction.payment_method,
        description=transaction.description,
        transaction_date=transaction.transaction_date,
        daily_record_id=transaction.daily_record_id,
        category_name=transaction.category.name if transaction.category else None,
        created_at=transaction.created_at,
    )


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
            detail="Transakcja nie znaleziona",
        )
