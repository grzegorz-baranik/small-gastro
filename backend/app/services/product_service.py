from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional
from decimal import Decimal
from app.models.product import Product, ProductIngredient
from app.models.ingredient import Ingredient
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductIngredientCreate,
    ProductIngredientUpdate,
)


def get_products(db: Session, skip: int = 0, limit: int = 100, active_only: bool = True) -> tuple[list[Product], int]:
    query = db.query(Product)
    if active_only:
        query = query.filter(Product.is_active == True)

    total = query.count()
    items = query.options(
        joinedload(Product.ingredients).joinedload(ProductIngredient.ingredient)
    ).offset(skip).limit(limit).all()
    return items, total


def get_product(db: Session, product_id: int) -> Optional[Product]:
    return db.query(Product).options(
        joinedload(Product.ingredients).joinedload(ProductIngredient.ingredient)
    ).filter(Product.id == product_id).first()


def get_product_by_name(db: Session, name: str) -> Optional[Product]:
    return db.query(Product).filter(Product.name == name).first()


def create_product(db: Session, product: ProductCreate) -> Product:
    db_product = Product(
        name=product.name,
        price=product.price,
    )
    db.add(db_product)
    db.flush()

    # Add ingredients if provided
    for ing in product.ingredients:
        db_pi = ProductIngredient(
            product_id=db_product.id,
            ingredient_id=ing.ingredient_id,
            quantity=ing.quantity,
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


def add_product_ingredient(
    db: Session,
    product_id: int,
    ingredient: ProductIngredientCreate
) -> Optional[ProductIngredient]:
    # Check product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None

    # Check ingredient exists
    ing = db.query(Ingredient).filter(Ingredient.id == ingredient.ingredient_id).first()
    if not ing:
        return None

    # Check if already exists
    existing = db.query(ProductIngredient).filter(
        ProductIngredient.product_id == product_id,
        ProductIngredient.ingredient_id == ingredient.ingredient_id
    ).first()
    if existing:
        existing.quantity = ingredient.quantity
        db.commit()
        db.refresh(existing)
        return existing

    db_pi = ProductIngredient(
        product_id=product_id,
        ingredient_id=ingredient.ingredient_id,
        quantity=ingredient.quantity,
    )
    db.add(db_pi)
    db.commit()
    db.refresh(db_pi)
    return db_pi


def update_product_ingredient(
    db: Session,
    product_id: int,
    ingredient_id: int,
    data: ProductIngredientUpdate
) -> Optional[ProductIngredient]:
    db_pi = db.query(ProductIngredient).filter(
        ProductIngredient.product_id == product_id,
        ProductIngredient.ingredient_id == ingredient_id
    ).first()

    if not db_pi:
        return None

    db_pi.quantity = data.quantity
    db.commit()
    db.refresh(db_pi)
    return db_pi


def remove_product_ingredient(db: Session, product_id: int, ingredient_id: int) -> bool:
    db_pi = db.query(ProductIngredient).filter(
        ProductIngredient.product_id == product_id,
        ProductIngredient.ingredient_id == ingredient_id
    ).first()

    if not db_pi:
        return False

    db.delete(db_pi)
    db.commit()
    return True
