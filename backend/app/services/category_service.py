from sqlalchemy.orm import Session
from typing import Optional
from app.models.expense_category import ExpenseCategory
from app.schemas.expense_category import (
    ExpenseCategoryCreate,
    ExpenseCategoryUpdate,
    ExpenseCategoryTree,
    ExpenseCategoryLeafResponse,
)
from app.core.i18n import t


# Use constants from model for single source of truth
MAX_CATEGORY_DEPTH = ExpenseCategory.MAX_DEPTH
LEAF_CATEGORY_LEVEL = ExpenseCategory.LEAF_LEVEL


class CategoryNotFoundError(Exception):
    """Raised when parent category does not exist."""
    pass


class MaxDepthExceededError(Exception):
    """Raised when category would exceed maximum depth."""
    pass


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
    # Fetch ALL categories in a single query to build paths in memory (avoids N+1)
    all_query = db.query(ExpenseCategory)
    if active_only:
        all_query = all_query.filter(ExpenseCategory.is_active == True)
    all_categories = all_query.all()

    # Build lookup map
    category_map = {c.id: c for c in all_categories}

    # Build response with full paths for leaf categories only
    result = []
    for category in all_categories:
        if category.level != LEAF_CATEGORY_LEVEL:
            continue

        # Build path by traversing parents in memory
        path_parts = [category.name]
        current = category
        while current.parent_id and current.parent_id in category_map:
            current = category_map[current.parent_id]
            path_parts.insert(0, current.name)

        result.append(
            ExpenseCategoryLeafResponse(
                id=category.id,
                name=category.name,
                parent_id=category.parent_id,
                level=category.level,
                is_active=category.is_active,
                full_path=" > ".join(path_parts),
            )
        )

    return sorted(result, key=lambda x: x.name)


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


def create_category(db: Session, category: ExpenseCategoryCreate) -> ExpenseCategory:
    level = 1
    if category.parent_id:
        parent = get_category(db, category.parent_id)
        if not parent:
            raise CategoryNotFoundError(t("errors.category_parent_not_found"))
        level = parent.level + 1
        if level > MAX_CATEGORY_DEPTH:
            raise MaxDepthExceededError(
                t("errors.category_max_depth", depth=MAX_CATEGORY_DEPTH)
            )

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
