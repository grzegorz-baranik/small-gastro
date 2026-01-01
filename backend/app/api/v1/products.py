from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
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
from app.schemas.product_variant import (
    ProductVariantCreate,
    ProductVariantUpdate,
    ProductVariantResponse,
    ProductVariantListResponse,
    ProductVariantWithIngredientsResponse,
    VariantIngredientCreate,
    VariantIngredientUpdate,
    VariantIngredientResponse,
    VariantIngredientListResponse,
)
from app.services import product_service
from app.services import product_variant_service

router = APIRouter()


@router.get("/", response_model=ProductListResponse)
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


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
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


# ---------------------------------------------------------------------------
# Product Variant Endpoints
# ---------------------------------------------------------------------------

@router.get("/{product_id}/variants", response_model=ProductVariantListResponse)
def list_product_variants(
    product_id: int,
    active_only: bool = Query(True, description="Tylko aktywne warianty"),
    db: Session = Depends(get_db),
):
    """Pobierz liste wariantow produktu."""
    # Verify product exists
    product = product_service.get_product(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produkt nie znaleziony",
        )

    items, total = product_variant_service.get_variants_for_product(db, product_id, active_only)
    response_items = [
        ProductVariantResponse(
            id=v.id,
            product_id=v.product_id,
            name=v.name,
            price=v.price,
            is_default=v.is_default,
            is_active=v.is_active,
            created_at=v.created_at,
            updated_at=v.updated_at,
        )
        for v in items
    ]
    return ProductVariantListResponse(items=response_items, total=total)


@router.post("/{product_id}/variants", response_model=ProductVariantResponse, status_code=status.HTTP_201_CREATED)
def create_product_variant(
    product_id: int,
    variant: ProductVariantCreate,
    db: Session = Depends(get_db),
):
    """Utworz nowy wariant produktu."""
    # Check if variant name already exists for this product
    existing = product_variant_service.get_variant_by_name(db, product_id, variant.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wariant o tej nazwie juz istnieje dla tego produktu",
        )

    created = product_variant_service.create_variant(db, product_id, variant)
    if not created:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produkt nie znaleziony",
        )

    return ProductVariantResponse(
        id=created.id,
        product_id=created.product_id,
        name=created.name,
        price=created.price,
        is_default=created.is_default,
        is_active=created.is_active,
        created_at=created.created_at,
        updated_at=created.updated_at,
    )


@router.get("/{product_id}/variants/{variant_id}", response_model=ProductVariantWithIngredientsResponse)
def get_product_variant(
    product_id: int,
    variant_id: int,
    db: Session = Depends(get_db),
):
    """Pobierz wariant produktu z przepisem (skladnikami)."""
    variant = product_variant_service.get_variant(db, variant_id)
    if not variant or variant.product_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wariant nie znaleziony",
        )

    ingredients = [
        VariantIngredientResponse(
            id=pi.id,
            ingredient_id=pi.ingredient_id,
            quantity=pi.quantity,
            is_primary=pi.is_primary,
            ingredient_name=pi.ingredient.name if pi.ingredient else None,
            ingredient_unit_type=pi.ingredient.unit_type.value if pi.ingredient else None,
            ingredient_unit_label=getattr(pi.ingredient, 'unit_label', None) if pi.ingredient else None,
        )
        for pi in variant.ingredients
    ]

    return ProductVariantWithIngredientsResponse(
        id=variant.id,
        product_id=variant.product_id,
        name=variant.name,
        price=variant.price,
        is_default=variant.is_default,
        is_active=variant.is_active,
        created_at=variant.created_at,
        updated_at=variant.updated_at,
        ingredients=ingredients,
    )


@router.put("/{product_id}/variants/{variant_id}", response_model=ProductVariantResponse)
def update_product_variant(
    product_id: int,
    variant_id: int,
    data: ProductVariantUpdate,
    db: Session = Depends(get_db),
):
    """Zaktualizuj wariant produktu."""
    # Verify the variant exists and belongs to the product
    variant = product_variant_service.get_variant(db, variant_id)
    if not variant or variant.product_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wariant nie znaleziony",
        )

    # Check if name change would cause conflict
    if data.name and data.name != variant.name:
        existing = product_variant_service.get_variant_by_name(db, product_id, data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Wariant o tej nazwie juz istnieje dla tego produktu",
            )

    updated = product_variant_service.update_variant(db, variant_id, data)
    return ProductVariantResponse(
        id=updated.id,
        product_id=updated.product_id,
        name=updated.name,
        price=updated.price,
        is_default=updated.is_default,
        is_active=updated.is_active,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


@router.delete("/{product_id}/variants/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_variant(
    product_id: int,
    variant_id: int,
    db: Session = Depends(get_db),
):
    """Dezaktywuj wariant produktu (soft delete)."""
    variant = product_variant_service.get_variant(db, variant_id)
    if not variant or variant.product_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wariant nie znaleziony",
        )

    product_variant_service.delete_variant(db, variant_id)


# ---------------------------------------------------------------------------
# Variant Ingredient (Recipe) Endpoints
# ---------------------------------------------------------------------------

@router.get("/variants/{variant_id}/ingredients", response_model=VariantIngredientListResponse)
def list_variant_ingredients(
    variant_id: int,
    db: Session = Depends(get_db),
):
    """Pobierz przepis (skladniki) wariantu."""
    variant = product_variant_service.get_variant(db, variant_id)
    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wariant nie znaleziony",
        )

    items, total = product_variant_service.get_variant_ingredients(db, variant_id)
    response_items = [
        VariantIngredientResponse(
            id=pi.id,
            ingredient_id=pi.ingredient_id,
            quantity=pi.quantity,
            is_primary=pi.is_primary,
            ingredient_name=pi.ingredient.name if pi.ingredient else None,
            ingredient_unit_type=pi.ingredient.unit_type.value if pi.ingredient else None,
            ingredient_unit_label=getattr(pi.ingredient, 'unit_label', None) if pi.ingredient else None,
        )
        for pi in items
    ]
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
            detail="Wariant lub skladnik nie znaleziony",
        )

    return VariantIngredientResponse(
        id=result.id,
        ingredient_id=result.ingredient_id,
        quantity=result.quantity,
        is_primary=result.is_primary,
        ingredient_name=result.ingredient.name if result.ingredient else None,
        ingredient_unit_type=result.ingredient.unit_type.value if result.ingredient else None,
        ingredient_unit_label=getattr(result.ingredient, 'unit_label', None) if result.ingredient else None,
    )


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
            detail="Skladnik nie znaleziony w przepisie wariantu",
        )

    return VariantIngredientResponse(
        id=result.id,
        ingredient_id=result.ingredient_id,
        quantity=result.quantity,
        is_primary=result.is_primary,
        ingredient_name=result.ingredient.name if result.ingredient else None,
        ingredient_unit_type=result.ingredient.unit_type.value if result.ingredient else None,
        ingredient_unit_label=getattr(result.ingredient, 'unit_label', None) if result.ingredient else None,
    )


@router.delete("/variants/{variant_id}/ingredients/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_variant_ingredient(
    variant_id: int,
    ingredient_id: int,
    db: Session = Depends(get_db),
):
    """Usun skladnik z przepisu wariantu."""
    result = product_variant_service.remove_variant_ingredient(db, variant_id, ingredient_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skladnik nie znaleziony w przepisie wariantu",
        )
