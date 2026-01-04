from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.api.deps import get_db
from app.core.i18n import t
from app.schemas.ingredient import (
    IngredientCreate,
    IngredientUpdate,
    IngredientResponse,
    IngredientListResponse,
)
from app.services import ingredient_service

router = APIRouter()


@router.get("", response_model=IngredientListResponse)
def list_ingredients(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = Query(None, description="Filtruj po statusie aktywnosci"),
    db: Session = Depends(get_db),
):
    """Pobierz liste wszystkich skladnikow."""
    items, total = ingredient_service.get_ingredients(db, skip, limit, is_active=is_active)
    return IngredientListResponse(items=items, total=total)


@router.post("", response_model=IngredientResponse, status_code=status.HTTP_201_CREATED)
def create_ingredient(
    ingredient: IngredientCreate,
    db: Session = Depends(get_db),
):
    """Utworz nowy skladnik."""
    existing = ingredient_service.get_ingredient_by_name(db, ingredient.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=t("errors.ingredient_exists"),
        )
    return ingredient_service.create_ingredient(db, ingredient)


@router.get("/{ingredient_id}", response_model=IngredientResponse)
def get_ingredient(
    ingredient_id: int,
    db: Session = Depends(get_db),
):
    """Pobierz skladnik po ID."""
    ingredient = ingredient_service.get_ingredient(db, ingredient_id)
    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.ingredient_not_found"),
        )
    return ingredient


@router.put("/{ingredient_id}", response_model=IngredientResponse)
def update_ingredient(
    ingredient_id: int,
    ingredient: IngredientUpdate,
    db: Session = Depends(get_db),
):
    """Zaktualizuj skladnik."""
    updated = ingredient_service.update_ingredient(db, ingredient_id, ingredient)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.ingredient_not_found"),
        )
    return updated


@router.delete("/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ingredient(
    ingredient_id: int,
    db: Session = Depends(get_db),
):
    """Usun skladnik."""
    deleted = ingredient_service.delete_ingredient(db, ingredient_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.ingredient_not_found"),
        )
