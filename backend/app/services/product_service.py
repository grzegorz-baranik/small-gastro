from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional
from decimal import Decimal
from app.models.product import Product, ProductVariant, ProductIngredient
from app.models.ingredient import Ingredient
from app.schemas.product import (
    ProductCreate,
    ProductSimpleCreate,
    ProductUpdate,
    ProductVariantCreate,
    ProductVariantUpdate,
    ProductIngredientCreate,
    ProductIngredientUpdate,
)


def get_products(db: Session, skip: int = 0, limit: int = 100, active_only: bool = True) -> tuple[list[Product], int]:
    query = db.query(Product)
    if active_only:
        query = query.filter(Product.is_active == True)

    total = query.count()
    items = query.options(
        joinedload(Product.variants).joinedload(ProductVariant.ingredients).joinedload(ProductIngredient.ingredient)
    ).offset(skip).limit(limit).all()
    return items, total


def get_product(db: Session, product_id: int) -> Optional[Product]:
    return db.query(Product).options(
        joinedload(Product.variants).joinedload(ProductVariant.ingredients).joinedload(ProductIngredient.ingredient)
    ).filter(Product.id == product_id).first()


def get_product_by_name(db: Session, name: str) -> Optional[Product]:
    return db.query(Product).filter(Product.name == name).first()


def create_product(db: Session, product: ProductCreate) -> Product:
    db_product = Product(
        name=product.name,
        has_variants=product.has_variants,
    )
    db.add(db_product)
    db.flush()

    # Add variants
    for variant_data in product.variants:
        db_variant = ProductVariant(
            product_id=db_product.id,
            name=variant_data.name,
            price_pln=variant_data.price_pln,
        )
        db.add(db_variant)
        db.flush()

        # Add ingredients to variant
        for ing in variant_data.ingredients:
            db_pi = ProductIngredient(
                product_variant_id=db_variant.id,
                ingredient_id=ing.ingredient_id,
                quantity=ing.quantity,
                is_primary=ing.is_primary,
            )
            db.add(db_pi)

    db.commit()
    db.refresh(db_product)
    return get_product(db, db_product.id)


def create_simple_product(db: Session, product: ProductSimpleCreate) -> Product:
    """Create a product with a single variant (no size variations)."""
    db_product = Product(
        name=product.name,
        has_variants=False,
    )
    db.add(db_product)
    db.flush()

    # Create single variant with no name
    db_variant = ProductVariant(
        product_id=db_product.id,
        name=None,
        price_pln=product.price_pln,
    )
    db.add(db_variant)
    db.flush()

    # Add ingredients
    for ing in product.ingredients:
        db_pi = ProductIngredient(
            product_variant_id=db_variant.id,
            ingredient_id=ing.ingredient_id,
            quantity=ing.quantity,
            is_primary=ing.is_primary,
        )
        db.add(db_pi)

    db.commit()
    db.refresh(db_product)
    return get_product(db, db_product.id)


def update_product(db: Session, product_id: int, product: ProductUpdate) -> Optional[Product]:
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        return None

    update_data = product.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)

    db.commit()
    return get_product(db, product_id)


def delete_product(db: Session, product_id: int) -> bool:
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        return False

    # Soft delete - just deactivate
    db_product.is_active = False
    db.commit()
    return True


def add_variant(db: Session, product_id: int, variant: ProductVariantCreate) -> Optional[ProductVariant]:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None

    db_variant = ProductVariant(
        product_id=product_id,
        name=variant.name,
        price_pln=variant.price_pln,
    )
    db.add(db_variant)
    db.flush()

    # Add ingredients
    for ing in variant.ingredients:
        db_pi = ProductIngredient(
            product_variant_id=db_variant.id,
            ingredient_id=ing.ingredient_id,
            quantity=ing.quantity,
            is_primary=ing.is_primary,
        )
        db.add(db_pi)

    # Mark product as having variants if it has multiple
    variant_count = db.query(ProductVariant).filter(ProductVariant.product_id == product_id).count()
    if variant_count > 1:
        product.has_variants = True

    db.commit()
    db.refresh(db_variant)
    return db_variant


def update_variant(db: Session, variant_id: int, variant: ProductVariantUpdate) -> Optional[ProductVariant]:
    db_variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not db_variant:
        return None

    update_data = variant.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_variant, field, value)

    db.commit()
    db.refresh(db_variant)
    return db_variant


def add_variant_ingredient(
    db: Session,
    variant_id: int,
    ingredient: ProductIngredientCreate
) -> Optional[ProductIngredient]:
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not variant:
        return None

    ing = db.query(Ingredient).filter(Ingredient.id == ingredient.ingredient_id).first()
    if not ing:
        return None

    # Check if already exists
    existing = db.query(ProductIngredient).filter(
        ProductIngredient.product_variant_id == variant_id,
        ProductIngredient.ingredient_id == ingredient.ingredient_id
    ).first()
    if existing:
        existing.quantity = ingredient.quantity
        existing.is_primary = ingredient.is_primary
        db.commit()
        db.refresh(existing)
        return existing

    db_pi = ProductIngredient(
        product_variant_id=variant_id,
        ingredient_id=ingredient.ingredient_id,
        quantity=ingredient.quantity,
        is_primary=ingredient.is_primary,
    )
    db.add(db_pi)
    db.commit()
    db.refresh(db_pi)
    return db_pi


def update_variant_ingredient(
    db: Session,
    variant_id: int,
    ingredient_id: int,
    data: ProductIngredientUpdate
) -> Optional[ProductIngredient]:
    db_pi = db.query(ProductIngredient).filter(
        ProductIngredient.product_variant_id == variant_id,
        ProductIngredient.ingredient_id == ingredient_id
    ).first()

    if not db_pi:
        return None

    db_pi.quantity = data.quantity
    if data.is_primary is not None:
        db_pi.is_primary = data.is_primary
    db.commit()
    db.refresh(db_pi)
    return db_pi


def remove_variant_ingredient(db: Session, variant_id: int, ingredient_id: int) -> bool:
    db_pi = db.query(ProductIngredient).filter(
        ProductIngredient.product_variant_id == variant_id,
        ProductIngredient.ingredient_id == ingredient_id
    ).first()

    if not db_pi:
        return False

    db.delete(db_pi)
    db.commit()
    return True
