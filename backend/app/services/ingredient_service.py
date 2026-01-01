from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from app.models.ingredient import Ingredient
from app.schemas.ingredient import IngredientCreate, IngredientUpdate


def get_ingredients(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None
) -> tuple[list[Ingredient], int]:
    query = db.query(Ingredient)

    if is_active is not None:
        query = query.filter(Ingredient.is_active == is_active)

    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total


def get_ingredient(db: Session, ingredient_id: int) -> Optional[Ingredient]:
    return db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()


def get_ingredient_by_name(db: Session, name: str) -> Optional[Ingredient]:
    return db.query(Ingredient).filter(Ingredient.name == name).first()


def create_ingredient(db: Session, ingredient: IngredientCreate) -> Ingredient:
    db_ingredient = Ingredient(
        name=ingredient.name,
        unit_type=ingredient.unit_type,
        unit_label=ingredient.unit_label,
        current_stock_grams=ingredient.current_stock_grams or 0,
        current_stock_count=ingredient.current_stock_count or 0,
        is_active=ingredient.is_active if ingredient.is_active is not None else True,
    )
    db.add(db_ingredient)
    db.commit()
    db.refresh(db_ingredient)
    return db_ingredient


def update_ingredient(db: Session, ingredient_id: int, ingredient: IngredientUpdate) -> Optional[Ingredient]:
    db_ingredient = get_ingredient(db, ingredient_id)
    if not db_ingredient:
        return None

    update_data = ingredient.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_ingredient, field, value)

    db.commit()
    db.refresh(db_ingredient)
    return db_ingredient


def delete_ingredient(db: Session, ingredient_id: int) -> bool:
    db_ingredient = get_ingredient(db, ingredient_id)
    if not db_ingredient:
        return False

    db.delete(db_ingredient)
    db.commit()
    return True
