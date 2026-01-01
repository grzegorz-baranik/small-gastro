from sqlalchemy.orm import Session
from typing import Optional
from app.models.expense_category import ExpenseCategory
from app.schemas.expense_category import (
    ExpenseCategoryCreate,
    ExpenseCategoryUpdate,
    ExpenseCategoryTree,
    ExpenseCategoryLeafResponse,
)


MAX_CATEGORY_DEPTH = 3
LEAF_CATEGORY_LEVEL = 3


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
    # Clear children first since model_validate picks them up from SQLAlchemy relationship
    category_map = {}
    for c in categories:
        tree_cat = ExpenseCategoryTree.model_validate(c)
        tree_cat.children = []  # Clear auto-loaded children to avoid duplicates
        category_map[c.id] = tree_cat

    roots = []

    for cat in categories:
        tree_cat = category_map[cat.id]
        if cat.parent_id is None:
            roots.append(tree_cat)
        elif cat.parent_id in category_map:
            category_map[cat.parent_id].children.append(tree_cat)

    return roots


def get_leaf_categories(db: Session, active_only: bool = True) -> list[ExpenseCategoryLeafResponse]:
    """Get only leaf categories (level 3) that can be assigned to transactions."""
    query = db.query(ExpenseCategory).filter(ExpenseCategory.level == LEAF_CATEGORY_LEVEL)
    if active_only:
        query = query.filter(ExpenseCategory.is_active == True)
    categories = query.order_by(ExpenseCategory.name).all()

    # Build response with full paths
    result = []
    for category in categories:
        full_path = get_category_path(db, category.id)
        result.append(
            ExpenseCategoryLeafResponse(
                id=category.id,
                name=category.name,
                parent_id=category.parent_id,
                level=category.level,
                is_active=category.is_active,
                full_path=full_path,
            )
        )
    return result


def get_category_path(db: Session, category_id: int) -> str:
    """Get full category path like 'Koszty operacyjne > Skladniki > Warzywa'."""
    category = db.query(ExpenseCategory).filter(ExpenseCategory.id == category_id).first()
    if not category:
        return ""

    path_parts = [category.name]
    current = category
    while current.parent_id:
        current = db.query(ExpenseCategory).filter(ExpenseCategory.id == current.parent_id).first()
        if current:
            path_parts.insert(0, current.name)
    return " > ".join(path_parts)


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
