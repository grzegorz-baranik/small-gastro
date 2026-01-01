from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.expense_category import (
    ExpenseCategoryCreate,
    ExpenseCategoryUpdate,
    ExpenseCategoryResponse,
    ExpenseCategoryTree,
    ExpenseCategoryLeafResponse,
)
from app.services import category_service

router = APIRouter()


@router.get("", response_model=list[ExpenseCategoryResponse])
def list_categories(
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    """Pobierz liste kategorii wydatkow."""
    return category_service.get_categories(db, active_only)


@router.get("/tree", response_model=list[ExpenseCategoryTree])
def get_category_tree(
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    """Pobierz drzewo kategorii wydatkow."""
    return category_service.get_category_tree(db, active_only)


@router.get("/leaves", response_model=list[ExpenseCategoryLeafResponse])
def get_leaf_categories(
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    """Pobierz tylko kategorie lisciowe (poziom 3) do przypisania do transakcji."""
    return category_service.get_leaf_categories(db, active_only)


@router.post("", response_model=ExpenseCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category: ExpenseCategoryCreate,
    db: Session = Depends(get_db),
):
    """Utworz nowa kategorie wydatkow."""
    result = category_service.create_category(db, category)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nie mozna utworzyc kategorii. Sprawdz czy kategoria nadrzedna istnieje i czy nie przekroczono maksymalnej glebokosci (3 poziomy).",
        )
    return result


@router.put("/{category_id}", response_model=ExpenseCategoryResponse)
def update_category(
    category_id: int,
    category: ExpenseCategoryUpdate,
    db: Session = Depends(get_db),
):
    """Zaktualizuj kategorie wydatkow."""
    result = category_service.update_category(db, category_id, category)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kategoria nie znaleziona",
        )
    return result


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
):
    """Dezaktywuj kategorie wydatkow."""
    result = category_service.delete_category(db, category_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nie mozna usunac kategorii. Upewnij sie, ze nie ma podkategorii.",
        )
