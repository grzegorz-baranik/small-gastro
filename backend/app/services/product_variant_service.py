from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional
from decimal import Decimal
from app.models.product import Product, ProductVariant, ProductIngredient
from app.models.ingredient import Ingredient
from app.schemas.product_variant import (
    ProductVariantCreate,
    ProductVariantUpdate,
    VariantIngredientCreate,
    VariantIngredientUpdate,
)


# ---------------------------------------------------------------------------
# Product Variant CRUD
# ---------------------------------------------------------------------------

def get_variants_for_product(
    db: Session,
    product_id: int,
    active_only: bool = True
) -> tuple[list[ProductVariant], int]:
    """Pobierz warianty produktu z przepisami (skladnikami)."""
    query = db.query(ProductVariant).filter(ProductVariant.product_id == product_id)

    if active_only:
        query = query.filter(ProductVariant.is_active == True)

    total = query.count()
    items = query.options(
        joinedload(ProductVariant.ingredients).joinedload(ProductIngredient.ingredient)
    ).order_by(ProductVariant.is_default.desc(), ProductVariant.name).all()
    return items, total


def get_variant(db: Session, variant_id: int) -> Optional[ProductVariant]:
    """Pobierz wariant po ID."""
    return db.query(ProductVariant).options(
        joinedload(ProductVariant.ingredients).joinedload(ProductIngredient.ingredient)
    ).filter(ProductVariant.id == variant_id).first()


def get_variant_by_name(
    db: Session,
    product_id: int,
    name: str
) -> Optional[ProductVariant]:
    """Pobierz wariant po nazwie w ramach produktu."""
    return db.query(ProductVariant).filter(
        ProductVariant.product_id == product_id,
        ProductVariant.name == name
    ).first()


def create_variant(
    db: Session,
    product_id: int,
    variant: ProductVariantCreate
) -> Optional[ProductVariant]:
    """Utworz nowy wariant produktu."""
    # Check if product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None

    db_variant = ProductVariant(
        product_id=product_id,
        name=variant.name,
        price_pln=variant.price_pln,
        is_default=variant.is_default or False,
        is_active=True,
    )

    # If this is set as default, unset other defaults
    if db_variant.is_default:
        db.query(ProductVariant).filter(
            ProductVariant.product_id == product_id,
            ProductVariant.is_default == True
        ).update({"is_default": False})

    db.add(db_variant)
    db.commit()
    db.refresh(db_variant)
    return db_variant


def update_variant(
    db: Session,
    variant_id: int,
    data: ProductVariantUpdate
) -> Optional[ProductVariant]:
    """Zaktualizuj wariant."""
    db_variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not db_variant:
        return None

    update_data = data.model_dump(exclude_unset=True)

    # If setting as default, unset other defaults first
    if update_data.get("is_default") is True:
        db.query(ProductVariant).filter(
            ProductVariant.product_id == db_variant.product_id,
            ProductVariant.id != variant_id,
            ProductVariant.is_default == True
        ).update({"is_default": False})

    for field, value in update_data.items():
        setattr(db_variant, field, value)

    db.commit()
    db.refresh(db_variant)
    return db_variant


def delete_variant(db: Session, variant_id: int) -> bool:
    """Dezaktywuj wariant (soft delete)."""
    db_variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not db_variant:
        return False

    db_variant.is_active = False
    db.commit()
    return True


# ---------------------------------------------------------------------------
# Variant Ingredient (Recipe) CRUD
# ---------------------------------------------------------------------------

def get_variant_ingredients(
    db: Session,
    variant_id: int
) -> tuple[list[ProductIngredient], int]:
    """Pobierz skladniki (przepis) wariantu."""
    query = db.query(ProductIngredient).filter(
        ProductIngredient.product_variant_id == variant_id
    ).options(
        joinedload(ProductIngredient.ingredient)
    )

    total = query.count()
    items = query.order_by(ProductIngredient.is_primary.desc()).all()
    return items, total


def add_variant_ingredient(
    db: Session,
    variant_id: int,
    data: VariantIngredientCreate
) -> Optional[ProductIngredient]:
    """Dodaj skladnik do przepisu wariantu."""
    # Verify variant exists
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not variant:
        return None

    # Verify ingredient exists
    ingredient = db.query(Ingredient).filter(Ingredient.id == data.ingredient_id).first()
    if not ingredient:
        return None

    # Check if already exists
    existing = db.query(ProductIngredient).filter(
        ProductIngredient.product_variant_id == variant_id,
        ProductIngredient.ingredient_id == data.ingredient_id
    ).first()

    if existing:
        # Update existing
        existing.quantity = data.quantity
        existing.is_primary = data.is_primary or False
        db.commit()
        db.refresh(existing)
        return existing

    # Check if this is the first ingredient - if so, make it primary automatically
    existing_count = db.query(ProductIngredient).filter(
        ProductIngredient.product_variant_id == variant_id
    ).count()

    # Auto-set primary if: explicitly requested OR this is the first ingredient
    should_be_primary = data.is_primary or (existing_count == 0)

    db_pi = ProductIngredient(
        product_variant_id=variant_id,
        ingredient_id=data.ingredient_id,
        quantity=data.quantity,
        is_primary=should_be_primary,
    )
    db.add(db_pi)
    db.commit()
    db.refresh(db_pi)
    return db_pi


def update_variant_ingredient(
    db: Session,
    variant_id: int,
    ingredient_id: int,
    data: VariantIngredientUpdate
) -> Optional[ProductIngredient]:
    """Zaktualizuj skladnik w przepisie wariantu."""
    db_pi = db.query(ProductIngredient).filter(
        ProductIngredient.product_variant_id == variant_id,
        ProductIngredient.ingredient_id == ingredient_id
    ).first()

    if not db_pi:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_pi, field, value)

    db.commit()
    db.refresh(db_pi)
    return db_pi


def remove_variant_ingredient(
    db: Session,
    variant_id: int,
    ingredient_id: int
) -> bool:
    """Usun skladnik z przepisu wariantu."""
    db_pi = db.query(ProductIngredient).filter(
        ProductIngredient.product_variant_id == variant_id,
        ProductIngredient.ingredient_id == ingredient_id
    ).first()

    if not db_pi:
        return False

    db.delete(db_pi)
    db.commit()
    return True
