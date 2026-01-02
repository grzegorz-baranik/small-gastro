from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.product import (
    ProductCreate,
    ProductSimpleCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    ProductVariantResponse,
    ProductIngredientResponse,
    ProductReorderRequest,
    ProductReorderResponse,
)
from app.services import product_service

router = APIRouter()


def _variant_to_response(variant) -> ProductVariantResponse:
    ing_responses = []
    for pi in variant.ingredients:
        ing_responses.append(ProductIngredientResponse(
            id=pi.id,
            ingredient_id=pi.ingredient_id,
            quantity=pi.quantity,
            is_primary=pi.is_primary,
            ingredient_name=pi.ingredient.name if pi.ingredient else None,
            ingredient_unit_type=pi.ingredient.unit_type.value if pi.ingredient else None,
        ))
    return ProductVariantResponse(
        id=variant.id,
        name=variant.name,
        price_pln=variant.price_pln,
        is_active=variant.is_active,
        ingredients=ing_responses,
        created_at=variant.created_at,
    )


def _product_to_response(product) -> ProductResponse:
    variant_responses = [_variant_to_response(v) for v in product.variants]
    return ProductResponse(
        id=product.id,
        name=product.name,
        has_variants=product.has_variants,
        is_active=product.is_active,
        sort_order=product.sort_order,
        variants=variant_responses,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


@router.get("", response_model=ProductListResponse)
def list_products(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    """Pobierz liste produktow."""
    items, total = product_service.get_products(db, skip, limit, active_only)
    response_items = [_product_to_response(p) for p in items]
    return ProductListResponse(items=response_items, total=total)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
):
    """Utworz nowy produkt z wariantami."""
    existing = product_service.get_product_by_name(db, product.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Produkt o tej nazwie juz istnieje",
        )
    created = product_service.create_product(db, product)
    return _product_to_response(created)


@router.post("/simple", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_simple_product(
    product: ProductSimpleCreate,
    db: Session = Depends(get_db),
):
    """Utworz prosty produkt z jedna cena (bez wariantow rozmiarow)."""
    existing = product_service.get_product_by_name(db, product.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Produkt o tej nazwie juz istnieje",
        )
    created = product_service.create_simple_product(db, product)
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


@router.put("/reorder", response_model=ProductReorderResponse)
def reorder_products(
    request: ProductReorderRequest,
    db: Session = Depends(get_db),
):
    """Zmien kolejnosc produktow w menu."""
    try:
        updated_count = product_service.reorder_products(db, request.product_ids)
        return ProductReorderResponse(
            message="Kolejnosc zaktualizowana",
            updated_count=updated_count,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


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
