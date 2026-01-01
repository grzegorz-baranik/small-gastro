from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    ProductIngredientCreate,
    ProductIngredientUpdate,
    ProductIngredientResponse,
)
from app.services import product_service

router = APIRouter()


@router.get("", response_model=ProductListResponse)
def list_products(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    """Pobierz liste produktow."""
    items, total = product_service.get_products(db, skip, limit, active_only)

    # Transform to include ingredient details
    response_items = []
    for product in items:
        ing_responses = []
        for pi in product.ingredients:
            ing_responses.append(ProductIngredientResponse(
                id=pi.id,
                ingredient_id=pi.ingredient_id,
                quantity=pi.quantity,
                ingredient_name=pi.ingredient.name if pi.ingredient else None,
                ingredient_unit_type=pi.ingredient.unit_type.value if pi.ingredient else None,
            ))
        response_items.append(ProductResponse(
            id=product.id,
            name=product.name,
            price=product.price,
            is_active=product.is_active,
            ingredients=ing_responses,
            created_at=product.created_at,
            updated_at=product.updated_at,
        ))

    return ProductListResponse(items=response_items, total=total)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
):
    """Utworz nowy produkt."""
    existing = product_service.get_product_by_name(db, product.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Produkt o tej nazwie juz istnieje",
        )
    created = product_service.create_product(db, product)
    return _product_to_response(created)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    """Pobierz produkt po ID."""
    product = product_service.get_product(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produkt nie znaleziony",
        )
    return _product_to_response(product)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product: ProductUpdate,
    db: Session = Depends(get_db),
):
    """Zaktualizuj produkt."""
    updated = product_service.update_product(db, product_id, product)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produkt nie znaleziony",
        )
    return _product_to_response(updated)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    """Dezaktywuj produkt."""
    deleted = product_service.delete_product(db, product_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produkt nie znaleziony",
        )


@router.post("/{product_id}/ingredients", response_model=ProductIngredientResponse, status_code=status.HTTP_201_CREATED)
def add_ingredient_to_product(
    product_id: int,
    ingredient: ProductIngredientCreate,
    db: Session = Depends(get_db),
):
    """Dodaj skladnik do produktu."""
    result = product_service.add_product_ingredient(db, product_id, ingredient)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produkt lub skladnik nie znaleziony",
        )
    return ProductIngredientResponse(
        id=result.id,
        ingredient_id=result.ingredient_id,
        quantity=result.quantity,
        ingredient_name=result.ingredient.name if result.ingredient else None,
        ingredient_unit_type=result.ingredient.unit_type.value if result.ingredient else None,
    )


@router.put("/{product_id}/ingredients/{ingredient_id}", response_model=ProductIngredientResponse)
def update_product_ingredient(
    product_id: int,
    ingredient_id: int,
    data: ProductIngredientUpdate,
    db: Session = Depends(get_db),
):
    """Zaktualizuj ilosc skladnika w produkcie."""
    result = product_service.update_product_ingredient(db, product_id, ingredient_id, data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Powiazanie produktu ze skladnikiem nie znalezione",
        )
    return ProductIngredientResponse(
        id=result.id,
        ingredient_id=result.ingredient_id,
        quantity=result.quantity,
        ingredient_name=result.ingredient.name if result.ingredient else None,
        ingredient_unit_type=result.ingredient.unit_type.value if result.ingredient else None,
    )


@router.delete("/{product_id}/ingredients/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_ingredient_from_product(
    product_id: int,
    ingredient_id: int,
    db: Session = Depends(get_db),
):
    """Usun skladnik z produktu."""
    result = product_service.remove_product_ingredient(db, product_id, ingredient_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Powiazanie produktu ze skladnikiem nie znalezione",
        )


def _product_to_response(product) -> ProductResponse:
    ing_responses = []
    for pi in product.ingredients:
        ing_responses.append(ProductIngredientResponse(
            id=pi.id,
            ingredient_id=pi.ingredient_id,
            quantity=pi.quantity,
            ingredient_name=pi.ingredient.name if pi.ingredient else None,
            ingredient_unit_type=pi.ingredient.unit_type.value if pi.ingredient else None,
        ))
    return ProductResponse(
        id=product.id,
        name=product.name,
        price=product.price,
        is_active=product.is_active,
        ingredients=ing_responses,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )
