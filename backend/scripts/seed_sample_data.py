#!/usr/bin/env python3
"""
Seed script for populating the database with sample data.

This script creates a complete sample dataset for a kebab shop including:
- Ingredients (meat, bread, sauces, etc.)
- Products with variants (kebabs, zapiekanki, hot-dogs, fries, drinks)
- Positions (employee roles)
- Employees with Polish names
- Shift templates for weekly schedules

Usage:
    # With Docker (after rebuilding):
    docker compose exec backend python scripts/seed_sample_data.py

    # Clear existing data first:
    docker compose exec backend python scripts/seed_sample_data.py --clear

    # Skip confirmation prompts:
    docker compose exec backend python scripts/seed_sample_data.py --clear --force

Options:
    --clear     Clear existing data before seeding (will prompt for confirmation)
    --force     Skip confirmation prompts
"""

import sys
import argparse
from decimal import Decimal
from datetime import time
from pathlib import Path

# Add parent directory to path for imports (handles both direct run and module run)
backend_dir = Path(__file__).parent.parent.resolve()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models import (
    Ingredient, UnitType,
    Product, ProductVariant, ProductIngredient,
    Position, Employee, ShiftTemplate,
    ProductCategory
)


def clear_data(db: Session, force: bool = False) -> None:
    """Clear all seeded data from the database."""
    from app.models import ShiftAssignment, CalculatedSale, InventorySnapshot, DeliveryItem, Delivery
    from app.models import StorageTransfer, Spoilage, StorageInventory, BatchDeduction, IngredientBatch
    from app.models import ShiftScheduleOverride, Transaction, SalesItem, DailyRecord, RecordedSale

    if not force:
        response = input("\n⚠️  This will DELETE all existing data. Continue? [y/N]: ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)

    print("Clearing existing data...")

    # Clear dependent tables first (respecting foreign key constraints)
    # Daily record related (must come before products and employees)
    db.query(RecordedSale).delete()
    db.query(CalculatedSale).delete()
    db.query(SalesItem).delete()
    db.query(BatchDeduction).delete()
    db.query(InventorySnapshot).delete()
    db.query(DeliveryItem).delete()
    db.query(Delivery).delete()
    db.query(StorageTransfer).delete()
    db.query(Spoilage).delete()
    db.query(ShiftAssignment).delete()

    # Employee-related
    db.query(ShiftScheduleOverride).delete()
    db.query(ShiftTemplate).delete()
    db.query(Transaction).filter(Transaction.employee_id.isnot(None)).update({"employee_id": None})

    # Product-related
    db.query(ProductIngredient).delete()
    db.query(ProductVariant).delete()
    db.query(Product).delete()
    db.query(ProductCategory).delete()

    # Ingredient-related
    db.query(IngredientBatch).delete()
    db.query(StorageInventory).delete()
    db.query(Ingredient).delete()

    # Daily records (after all dependencies)
    db.query(DailyRecord).delete()

    # Core entities
    db.query(Employee).delete()
    db.query(Position).delete()

    db.commit()
    print("✓ Data cleared")


def seed_categories(db: Session) -> dict[str, ProductCategory]:
    """Seed product categories for the sales entry UI."""
    print("\nSeeding product categories...")

    categories_data = [
        {"name": "Kebaby", "sort_order": 1},
        {"name": "Zapiekanki", "sort_order": 2},
        {"name": "Hot-Dogi", "sort_order": 3},
        {"name": "Napoje", "sort_order": 4},
        {"name": "Dodatki", "sort_order": 5},
    ]

    categories = {}
    for data in categories_data:
        category = ProductCategory(**data)
        db.add(category)
        db.flush()
        categories[data["name"]] = category
        print(f"  + {data['name']}")

    db.commit()
    print(f"✓ Created {len(categories)} categories")
    return categories


def seed_ingredients(db: Session) -> dict[str, Ingredient]:
    """Seed ingredients and return a dictionary for reference."""
    print("\nSeeding ingredients...")

    ingredients_data = [
        # Meat (weight-based, in kg)
        {"name": "Mięso kurczak", "unit_type": UnitType.WEIGHT, "unit_label": "kg"},
        {"name": "Mięso wołowina", "unit_type": UnitType.WEIGHT, "unit_label": "kg"},
        {"name": "Kiełbasa hot-dog", "unit_type": UnitType.COUNT, "unit_label": "szt"},

        # Bread (count-based)
        {"name": "Chleb pita", "unit_type": UnitType.COUNT, "unit_label": "szt"},
        {"name": "Tortilla", "unit_type": UnitType.COUNT, "unit_label": "szt"},
        {"name": "Pojemnik box", "unit_type": UnitType.COUNT, "unit_label": "szt"},
        {"name": "Bagietka", "unit_type": UnitType.COUNT, "unit_label": "szt"},
        {"name": "Bułka hot-dog", "unit_type": UnitType.COUNT, "unit_label": "szt"},

        # Sauces (weight-based, in liters tracked as kg)
        {"name": "Sos łagodny", "unit_type": UnitType.WEIGHT, "unit_label": "L"},
        {"name": "Sos średni", "unit_type": UnitType.WEIGHT, "unit_label": "L"},
        {"name": "Sos ostry", "unit_type": UnitType.WEIGHT, "unit_label": "L"},

        # Zapiekanka toppings (weight-based)
        {"name": "Ser żółty", "unit_type": UnitType.WEIGHT, "unit_label": "kg"},
        {"name": "Szynka", "unit_type": UnitType.WEIGHT, "unit_label": "kg"},
        {"name": "Pieczarki", "unit_type": UnitType.WEIGHT, "unit_label": "kg"},

        # Fries (count-based portions)
        {"name": "Frytki mrożone", "unit_type": UnitType.COUNT, "unit_label": "porcja"},

        # Drinks (count-based)
        {"name": "Cola 0.33L", "unit_type": UnitType.COUNT, "unit_label": "szt"},
        {"name": "Cola 0.5L", "unit_type": UnitType.COUNT, "unit_label": "szt"},
        {"name": "Fanta 0.33L", "unit_type": UnitType.COUNT, "unit_label": "szt"},
        {"name": "Fanta 0.5L", "unit_type": UnitType.COUNT, "unit_label": "szt"},
        {"name": "Sprite 0.33L", "unit_type": UnitType.COUNT, "unit_label": "szt"},
        {"name": "Sprite 0.5L", "unit_type": UnitType.COUNT, "unit_label": "szt"},
        {"name": "Nestea 0.33L", "unit_type": UnitType.COUNT, "unit_label": "szt"},
        {"name": "Nestea 0.5L", "unit_type": UnitType.COUNT, "unit_label": "szt"},
        {"name": "Woda niegazowana 0.5L", "unit_type": UnitType.COUNT, "unit_label": "szt"},
        {"name": "Woda gazowana 0.5L", "unit_type": UnitType.COUNT, "unit_label": "szt"},
        {"name": "Sok pomarańczowy 0.33L", "unit_type": UnitType.COUNT, "unit_label": "szt"},
        {"name": "Sok jabłkowy 0.33L", "unit_type": UnitType.COUNT, "unit_label": "szt"},
    ]

    ingredients = {}
    for data in ingredients_data:
        ingredient = Ingredient(**data)
        db.add(ingredient)
        db.flush()
        ingredients[data["name"]] = ingredient
        print(f"  + {data['name']}")

    db.commit()
    print(f"✓ Created {len(ingredients)} ingredients")
    return ingredients


def seed_products(db: Session, ingredients: dict[str, Ingredient], categories: dict[str, ProductCategory]) -> None:
    """Seed products with variants, ingredient links, and category assignments."""
    print("\nSeeding products...")

    product_count = 0
    variant_count = 0

    # ============================================
    # KEBABS
    # ============================================
    # Kebab structure: 2 meat types × 3 sizes × 3 serving styles = 18 variants
    # But we'll create it as: 6 products (meat × style) with 3 size variants each

    kebab_configs = [
        # (product_name, meat_ingredient, serving_ingredient, base_prices)
        ("Kebab Kurczak Pita", "Mięso kurczak", "Chleb pita", [22, 28, 35]),
        ("Kebab Kurczak Tortilla", "Mięso kurczak", "Tortilla", [24, 30, 37]),
        ("Kebab Kurczak Box", "Mięso kurczak", "Pojemnik box", [26, 32, 39]),
        ("Kebab Wołowina Pita", "Mięso wołowina", "Chleb pita", [22, 28, 35]),
        ("Kebab Wołowina Tortilla", "Mięso wołowina", "Tortilla", [24, 30, 37]),
        ("Kebab Wołowina Box", "Mięso wołowina", "Pojemnik box", [26, 32, 39]),
    ]

    size_configs = [
        # (name, meat_kg, sauce_L)
        ("Mały", Decimal("0.100"), Decimal("0.020")),
        ("Średni", Decimal("0.150"), Decimal("0.030")),
        ("Duży", Decimal("0.200"), Decimal("0.040")),
    ]

    for idx, (product_name, meat_name, serving_name, prices) in enumerate(kebab_configs):
        product = Product(
            name=product_name,
            has_variants=True,
            sort_order=idx + 1,
            category_id=categories["Kebaby"].id
        )
        db.add(product)
        db.flush()
        product_count += 1

        for size_idx, ((size_name, meat_qty, sauce_qty), price) in enumerate(zip(size_configs, prices)):
            variant = ProductVariant(
                product_id=product.id,
                name=size_name,
                price_pln=Decimal(price),
                is_default=(size_idx == 1)  # Średni is default
            )
            db.add(variant)
            db.flush()
            variant_count += 1

            # Link ingredients
            # Primary: meat
            db.add(ProductIngredient(
                product_variant_id=variant.id,
                ingredient_id=ingredients[meat_name].id,
                quantity=meat_qty,
                is_primary=True
            ))
            # Serving container
            db.add(ProductIngredient(
                product_variant_id=variant.id,
                ingredient_id=ingredients[serving_name].id,
                quantity=Decimal("1")
            ))
            # Sauce (using średni sauce as default)
            db.add(ProductIngredient(
                product_variant_id=variant.id,
                ingredient_id=ingredients["Sos średni"].id,
                quantity=sauce_qty
            ))

    print(f"  + Kebaby (6 products × 3 sizes)")

    # ============================================
    # ZAPIEKANKI
    # ============================================
    zapiekanka_configs = [
        # (topping_name, half_price, full_price, topping_ingredient, topping_qty_half, topping_qty_full)
        ("Zapiekanka Ser", 10, 18, None, None, None),
        ("Zapiekanka Szynka", 12, 20, "Szynka", Decimal("0.050"), Decimal("0.100")),
        ("Zapiekanka Kurczak", 14, 24, "Mięso kurczak", Decimal("0.060"), Decimal("0.120")),
        ("Zapiekanka Pieczarki", 11, 19, "Pieczarki", Decimal("0.040"), Decimal("0.080")),
    ]

    for idx, (name, half_price, full_price, topping_ing, half_qty, full_qty) in enumerate(zapiekanka_configs):
        product = Product(
            name=name,
            has_variants=True,
            sort_order=20 + idx,
            category_id=categories["Zapiekanki"].id
        )
        db.add(product)
        db.flush()
        product_count += 1

        for size_idx, (size_name, price, topping_qty) in enumerate([
            ("Połówka", half_price, half_qty),
            ("Cała", full_price, full_qty)
        ]):
            variant = ProductVariant(
                product_id=product.id,
                name=size_name,
                price_pln=Decimal(price),
                is_default=(size_idx == 1)
            )
            db.add(variant)
            db.flush()
            variant_count += 1

            # Bagietka (primary for all)
            db.add(ProductIngredient(
                product_variant_id=variant.id,
                ingredient_id=ingredients["Bagietka"].id,
                quantity=Decimal("0.5") if size_name == "Połówka" else Decimal("1"),
                is_primary=True
            ))
            # Cheese
            db.add(ProductIngredient(
                product_variant_id=variant.id,
                ingredient_id=ingredients["Ser żółty"].id,
                quantity=Decimal("0.030") if size_name == "Połówka" else Decimal("0.060")
            ))
            # Optional topping
            if topping_ing and topping_qty:
                db.add(ProductIngredient(
                    product_variant_id=variant.id,
                    ingredient_id=ingredients[topping_ing].id,
                    quantity=topping_qty
                ))

    print(f"  + Zapiekanki (4 toppings × 2 sizes)")

    # ============================================
    # HOT-DOG
    # ============================================
    product = Product(name="Hot-Dog", has_variants=False, sort_order=30, category_id=categories["Hot-Dogi"].id)
    db.add(product)
    db.flush()
    product_count += 1

    variant = ProductVariant(
        product_id=product.id,
        name=None,  # No variant name for single-size
        price_pln=Decimal("12"),
        is_default=True
    )
    db.add(variant)
    db.flush()
    variant_count += 1

    db.add(ProductIngredient(
        product_variant_id=variant.id,
        ingredient_id=ingredients["Kiełbasa hot-dog"].id,
        quantity=Decimal("1"),
        is_primary=True
    ))
    db.add(ProductIngredient(
        product_variant_id=variant.id,
        ingredient_id=ingredients["Bułka hot-dog"].id,
        quantity=Decimal("1")
    ))
    print(f"  + Hot-Dog")

    # ============================================
    # FRYTKI
    # ============================================
    product = Product(name="Frytki", has_variants=True, sort_order=31, category_id=categories["Dodatki"].id)
    db.add(product)
    db.flush()
    product_count += 1

    for size_idx, (size_name, price, portion_count) in enumerate([
        ("Małe", 8, Decimal("1")),
        ("Duże", 12, Decimal("2"))  # Large = 2 portions
    ]):
        variant = ProductVariant(
            product_id=product.id,
            name=size_name,
            price_pln=Decimal(price),
            is_default=(size_idx == 0)
        )
        db.add(variant)
        db.flush()
        variant_count += 1

        db.add(ProductIngredient(
            product_variant_id=variant.id,
            ingredient_id=ingredients["Frytki mrożone"].id,
            quantity=portion_count,
            is_primary=True
        ))
    print(f"  + Frytki (2 sizes)")

    # ============================================
    # DRINKS
    # ============================================
    drink_configs = [
        # (name, size, price, ingredient_name)
        ("Cola", "0.33L", 5, "Cola 0.33L"),
        ("Cola", "0.5L", 7, "Cola 0.5L"),
        ("Fanta", "0.33L", 5, "Fanta 0.33L"),
        ("Fanta", "0.5L", 7, "Fanta 0.5L"),
        ("Sprite", "0.33L", 5, "Sprite 0.33L"),
        ("Sprite", "0.5L", 7, "Sprite 0.5L"),
        ("Nestea", "0.33L", 5, "Nestea 0.33L"),
        ("Nestea", "0.5L", 7, "Nestea 0.5L"),
        ("Woda niegazowana", "0.5L", 4, "Woda niegazowana 0.5L"),
        ("Woda gazowana", "0.5L", 4, "Woda gazowana 0.5L"),
        ("Sok pomarańczowy", "0.33L", 5, "Sok pomarańczowy 0.33L"),
        ("Sok jabłkowy", "0.33L", 5, "Sok jabłkowy 0.33L"),
    ]

    # Group drinks by name for multi-variant products
    drink_groups = {}
    for name, size, price, ing_name in drink_configs:
        if name not in drink_groups:
            drink_groups[name] = []
        drink_groups[name].append((size, price, ing_name))

    for idx, (drink_name, sizes) in enumerate(drink_groups.items()):
        has_variants = len(sizes) > 1
        product = Product(
            name=drink_name,
            has_variants=has_variants,
            sort_order=40 + idx,
            category_id=categories["Napoje"].id
        )
        db.add(product)
        db.flush()
        product_count += 1

        for size_idx, (size, price, ing_name) in enumerate(sizes):
            variant = ProductVariant(
                product_id=product.id,
                name=size if has_variants else None,
                price_pln=Decimal(price),
                is_default=(size_idx == 0)
            )
            db.add(variant)
            db.flush()
            variant_count += 1

            db.add(ProductIngredient(
                product_variant_id=variant.id,
                ingredient_id=ingredients[ing_name].id,
                quantity=Decimal("1"),
                is_primary=True
            ))

    print(f"  + Napoje (8 drink types)")

    db.commit()
    print(f"✓ Created {product_count} products with {variant_count} variants")


def seed_positions(db: Session) -> dict[str, Position]:
    """Seed employee positions."""
    print("\nSeeding positions...")

    positions_data = [
        {"name": "Właściciel", "hourly_rate": Decimal("0")},  # Owner uses daily rate, not hourly
        {"name": "Pracownik", "hourly_rate": Decimal("27")},  # Mid-range: 25-30 PLN/hour
    ]

    positions = {}
    for data in positions_data:
        position = Position(**data)
        db.add(position)
        db.flush()
        positions[data["name"]] = position
        print(f"  + {data['name']} ({data['hourly_rate']} PLN/h)")

    db.commit()
    print(f"✓ Created {len(positions)} positions")
    return positions


def seed_employees(db: Session, positions: dict[str, Position]) -> dict[str, Employee]:
    """Seed employees with Polish names."""
    print("\nSeeding employees...")

    employees_data = [
        # Owner with fixed daily rate (tracked elsewhere, hourly_rate_override = 0)
        {"name": "Tomasz Kowalski", "position": "Właściciel", "hourly_rate_override": Decimal("0")},
        # Staff with hourly rates
        {"name": "Anna Nowak", "position": "Pracownik", "hourly_rate_override": Decimal("28")},
        {"name": "Piotr Wiśniewski", "position": "Pracownik", "hourly_rate_override": Decimal("26")},
    ]

    employees = {}
    for data in employees_data:
        employee = Employee(
            name=data["name"],
            position_id=positions[data["position"]].id,
            hourly_rate_override=data.get("hourly_rate_override")
        )
        db.add(employee)
        db.flush()
        employees[data["name"]] = employee
        rate = data.get("hourly_rate_override") or positions[data["position"]].hourly_rate
        print(f"  + {data['name']} ({data['position']}, {rate} PLN/h)")

    db.commit()
    print(f"✓ Created {len(employees)} employees")
    return employees


def seed_shift_templates(db: Session, employees: dict[str, Employee]) -> None:
    """Seed shift templates for weekly schedules."""
    print("\nSeeding shift templates...")

    # Operating hours: 10:00 - 20:00, Monday-Saturday (0-5)
    # Shift patterns:
    #   - Tomasz (owner): Full day Mon-Sat 10:00-20:00
    #   - Anna: Morning Mon-Sat 10:00-15:00 (overlaps with Piotr 14:00-15:00)
    #   - Piotr: Afternoon Mon-Sat 14:00-20:00 (overlaps with Anna 14:00-15:00)

    templates_data = [
        # Owner - full day, all days
        *[{"employee": "Tomasz Kowalski", "day": d, "start": time(10, 0), "end": time(20, 0)}
          for d in range(6)],  # Mon-Sat

        # Anna - morning shift
        *[{"employee": "Anna Nowak", "day": d, "start": time(10, 0), "end": time(15, 0)}
          for d in range(6)],  # Mon-Sat

        # Piotr - afternoon shift
        *[{"employee": "Piotr Wiśniewski", "day": d, "start": time(14, 0), "end": time(20, 0)}
          for d in range(6)],  # Mon-Sat
    ]

    day_names = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Niedz"]

    template_count = 0
    for data in templates_data:
        template = ShiftTemplate(
            employee_id=employees[data["employee"]].id,
            day_of_week=data["day"],
            start_time=data["start"],
            end_time=data["end"]
        )
        db.add(template)
        template_count += 1

    db.commit()

    # Print summary by employee
    for emp_name, emp in employees.items():
        days = [t for t in templates_data if t["employee"] == emp_name]
        if days:
            day_range = f"{day_names[days[0]['day']]}-{day_names[days[-1]['day']]}"
            time_range = f"{days[0]['start'].strftime('%H:%M')}-{days[0]['end'].strftime('%H:%M')}"
            print(f"  + {emp_name}: {day_range} {time_range}")

    print(f"✓ Created {template_count} shift templates")


def main():
    parser = argparse.ArgumentParser(description="Seed sample data for small-gastro")
    parser.add_argument("--clear", action="store_true", help="Clear existing data before seeding")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompts")
    args = parser.parse_args()

    print("=" * 50)
    print("  Small Gastro - Sample Data Seeder")
    print("=" * 50)

    db = SessionLocal()

    try:
        if args.clear:
            clear_data(db, force=args.force)

        categories = seed_categories(db)
        ingredients = seed_ingredients(db)
        seed_products(db, ingredients, categories)
        positions = seed_positions(db)
        employees = seed_employees(db, positions)
        seed_shift_templates(db, employees)

        print("\n" + "=" * 50)
        print("  ✅ Sample data seeded successfully!")
        print("=" * 50)

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
