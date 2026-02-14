from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.i18n import t
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
from app.schemas.product_variant import (
    ProductVariantCreate,
    ProductVariantUpdate,
    ProductVariantListResponse,
    ProductVariantWithIngredientsResponse,
    VariantIngredientCreate,
    VariantIngredientUpdate,
    VariantIngredientResponse,
    VariantIngredientListResponse,
)
from app.services import product_service, product_variant_service

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
            detail=t("errors.product_exists"),
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
            detail=t("errors.product_exists"),
        )
    created = product_service.create_simple_product(db, product)
    return _product_to_response(created)


@router.put("/reorder", response_model=ProductReorderResponse)
def reorder_products(
    request: ProductReorderRequest,
    db: Session = Depends(get_db),
):
    """Zmien kolejnosc produktow w menu."""
    try:
        updated_count = product_service.reorder_products(db, request.product_ids)
        return ProductReorderResponse(
            message=t("success.order_updated"),
            updated_count=updated_count,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


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
            detail=t("errors.product_not_found"),
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
            detail=t("errors.product_not_found"),
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
            detail=t("errors.product_not_found"),
        )


# ---------------------------------------------------------------------------
# Product Variant Endpoints
# ---------------------------------------------------------------------------

def _variant_ingredient_to_response(pi) -> VariantIngredientResponse:
    """Convert ProductIngredient model to response schema."""
    return VariantIngredientResponse(
        id=pi.id,
        ingredient_id=pi.ingredient_id,
        quantity=pi.quantity,
        is_primary=pi.is_primary,
        ingredient_name=pi.ingredient.name if pi.ingredient else None,
        ingredient_unit_type=pi.ingredient.unit_type.value if pi.ingredient else None,
        ingredient_unit_label=pi.ingredient.unit_label if pi.ingredient else None,
    )


def _variant_to_full_response(variant) -> ProductVariantWithIngredientsResponse:
    """Convert ProductVariant model to full response with ingredients."""
    ingredients = [_variant_ingredient_to_response(pi) for pi in variant.ingredients]
    return ProductVariantWithIngredientsResponse(
        id=variant.id,
        product_id=variant.product_id,
        name=variant.name,
        price_pln=variant.price_pln,
        is_default=variant.is_default,
        is_active=variant.is_active,
        created_at=variant.created_at,
        updated_at=variant.updated_at,
        ingredients=ingredients,
    )


@router.get("/{product_id}/variants", response_model=ProductVariantListResponse)
def list_variants(
    product_id: int,
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
):
    """Pobierz liste wariantow produktu."""
    # Verify product exists
    product = product_service.get_product(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.product_not_found"),
        )

    items, total = product_variant_service.get_variants_for_product(db, product_id, active_only)
    response_items = [_variant_to_full_response(v) for v in items]
    return ProductVariantListResponse(items=response_items, total=total)


@router.get("/{product_id}/variants/{variant_id}", response_model=ProductVariantWithIngredientsResponse)
def get_variant(
    product_id: int,
    variant_id: int,
    db: Session = Depends(get_db),
):
    """Pobierz wariant po ID z lista skladnikow."""
    variant = product_variant_service.get_variant(db, variant_id)
    if not variant or variant.product_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.variant_not_found"),
        )
    return _variant_to_full_response(variant)


@router.post("/{product_id}/variants", response_model=ProductVariantWithIngredientsResponse, status_code=status.HTTP_201_CREATED)
def create_variant(
    product_id: int,
    variant: ProductVariantCreate,
    db: Session = Depends(get_db),
):
    """Utworz nowy wariant produktu."""
    created = product_variant_service.create_variant(db, product_id, variant)
    if not created:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.product_not_found"),
        )
    # Refresh to get relationships
    refreshed = product_variant_service.get_variant(db, created.id)
    return _variant_to_full_response(refreshed)


@router.put("/{product_id}/variants/{variant_id}", response_model=ProductVariantWithIngredientsResponse)
def update_variant(
    product_id: int,
    variant_id: int,
    data: ProductVariantUpdate,
    db: Session = Depends(get_db),
):
    """Zaktualizuj wariant."""
    # Verify variant belongs to product
    existing = product_variant_service.get_variant(db, variant_id)
    if not existing or existing.product_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.variant_not_found"),
        )

    updated = product_variant_service.update_variant(db, variant_id, data)
    refreshed = product_variant_service.get_variant(db, updated.id)
    return _variant_to_full_response(refreshed)


@router.delete("/{product_id}/variants/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_variant(
    product_id: int,
    variant_id: int,
    db: Session = Depends(get_db),
):
    """Dezaktywuj wariant (soft delete)."""
    # Verify variant belongs to product
    existing = product_variant_service.get_variant(db, variant_id)
    if not existing or existing.product_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.variant_not_found"),
        )

    deleted = product_variant_service.delete_variant(db, variant_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.variant_not_found"),
        )


# ---------------------------------------------------------------------------
# Variant Ingredient (Recipe) Endpoints
# ---------------------------------------------------------------------------

@router.get("/variants/{variant_id}/ingredients", response_model=VariantIngredientListResponse)
def list_variant_ingredients(
    variant_id: int,
    db: Session = Depends(get_db),
):
    """Pobierz przepis (liste skladnikow) wariantu."""
    variant = product_variant_service.get_variant(db, variant_id)
    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.variant_not_found"),
        )

    items, total = product_variant_service.get_variant_ingredients(db, variant_id)
    response_items = [_variant_ingredient_to_response(pi) for pi in items]
    return VariantIngredientListResponse(items=response_items, total=total)


@router.post("/variants/{variant_id}/ingredients", response_model=VariantIngredientResponse, status_code=status.HTTP_201_CREATED)
def add_variant_ingredient(
    variant_id: int,
    data: VariantIngredientCreate,
    db: Session = Depends(get_db),
):
    """Dodaj skladnik do przepisu wariantu."""
    result = product_variant_service.add_variant_ingredient(db, variant_id, data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.variant_or_ingredient_not_found"),
        )

    # Refresh to get ingredient relationship
    items, _ = product_variant_service.get_variant_ingredients(db, variant_id)
    for pi in items:
        if pi.ingredient_id == data.ingredient_id:
            return _variant_ingredient_to_response(pi)
    return _variant_ingredient_to_response(result)


@router.put("/variants/{variant_id}/ingredients/{ingredient_id}", response_model=VariantIngredientResponse)
def update_variant_ingredient(
    variant_id: int,
    ingredient_id: int,
    data: VariantIngredientUpdate,
    db: Session = Depends(get_db),
):
    """Zaktualizuj skladnik w przepisie wariantu."""
    result = product_variant_service.update_variant_ingredient(db, variant_id, ingredient_id, data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.ingredient_not_in_recipe"),
        )

    # Refresh to get ingredient relationship
    items, _ = product_variant_service.get_variant_ingredients(db, variant_id)
    for pi in items:
        if pi.ingredient_id == ingredient_id:
            return _variant_ingredient_to_response(pi)
    return _variant_ingredient_to_response(result)


@router.delete("/variants/{variant_id}/ingredients/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_variant_ingredient(
    variant_id: int,
    ingredient_id: int,
    db: Session = Depends(get_db),
):
    """Usun skladnik z przepisu wariantu."""
    deleted = product_variant_service.remove_variant_ingredient(db, variant_id, ingredient_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.ingredient_not_in_recipe"),
        )
