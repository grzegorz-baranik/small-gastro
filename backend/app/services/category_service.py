from sqlalchemy.orm import Session
from typing import Optional
from app.models.expense_category import ExpenseCategory
from app.schemas.expense_category import ExpenseCategoryCreate, ExpenseCategoryUpdate, ExpenseCategoryTree


MAX_CATEGORY_DEPTH = 3


def get_categories(db: Session, active_only: bool = True) -> list[ExpenseCategory]:
    query = db.query(ExpenseCategory)
    if active_only:
        query = query.filter(ExpenseCategory.is_active == True)
    return query.order_by(ExpenseCategory.level, ExpenseCategory.name).all()


def get_category(db: Session, category_id: int) -> Optional[ExpenseCategory]:
    return db.query(ExpenseCategory).filter(ExpenseCategory.id == category_id).first()


def get_category_tree(db: Session, active_only: bool = True) -> list[ExpenseCategoryTree]:
    categories = get_categories(db, active_only)

    # Build tree structure
    category_map = {c.id: ExpenseCategoryTree.model_validate(c) for c in categories}
    roots = []

    for cat in categories:
        tree_cat = category_map[cat.id]
        if cat.parent_id is None:
            roots.append(tree_cat)
        elif cat.parent_id in category_map:
            category_map[cat.parent_id].children.append(tree_cat)

    return roots


def create_category(db: Session, category: ExpenseCategoryCreate) -> Optional[ExpenseCategory]:
    level = 1
    if category.parent_id:
        parent = get_category(db, category.parent_id)
        if not parent:
            return None
        level = parent.level + 1
        if level > MAX_CATEGORY_DEPTH:
            return None

    db_category = ExpenseCategory(
        name=category.name,
        parent_id=category.parent_id,
        level=level,
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def update_category(db: Session, category_id: int, category: ExpenseCategoryUpdate) -> Optional[ExpenseCategory]:
    db_category = get_category(db, category_id)
    if not db_category:
        return None

    update_data = category.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)

    db.commit()
    db.refresh(db_category)
    return db_category


def delete_category(db: Session, category_id: int) -> bool:
    db_category = get_category(db, category_id)
    if not db_category:
        return False

    # Check if has children or transactions
    has_children = db.query(ExpenseCategory).filter(ExpenseCategory.parent_id == category_id).first()
    if has_children:
        return False

    # Soft delete
    db_category.is_active = False
    db.commit()
    return True
