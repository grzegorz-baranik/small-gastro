from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional
from decimal import Decimal
from app.models.sales_item import SalesItem
from app.models.product import Product, ProductVariant
from app.models.daily_record import DailyRecord, DayStatus
from app.schemas.sales import SalesItemCreate, SalesItemResponse, DailySalesSummary


def get_sales_for_day(db: Session, daily_record_id: int) -> list[SalesItem]:
    return db.query(SalesItem).filter(
        SalesItem.daily_record_id == daily_record_id
    ).all()


def get_today_sales(db: Session) -> Optional[DailySalesSummary]:
    from datetime import date
    today = date.today()

    record = db.query(DailyRecord).filter(DailyRecord.date == today).first()
    if not record:
        return None

    return get_daily_sales_summary(db, record.id)


def get_daily_sales_summary(db: Session, daily_record_id: int) -> Optional[DailySalesSummary]:
    record = db.query(DailyRecord).filter(DailyRecord.id == daily_record_id).first()
    if not record:
        return None

    sales = get_sales_for_day(db, daily_record_id)

    items = []
    total_items = 0
    total_revenue = Decimal("0")

    for sale in sales:
        product = db.query(Product).filter(Product.id == sale.product_id).first()
        items.append(SalesItemResponse(
            id=sale.id,
            daily_record_id=sale.daily_record_id,
            product_id=sale.product_id,
            product_name=product.name if product else None,
            quantity_sold=sale.quantity_sold,
            unit_price=sale.unit_price,
            total_price=sale.total_price,
            created_at=sale.created_at,
        ))
        total_items += sale.quantity_sold
        total_revenue += sale.total_price

    return DailySalesSummary(
        daily_record_id=daily_record_id,
        date=str(record.date),
        items=items,
        total_items_sold=total_items,
        total_revenue=total_revenue,
    )


def create_sale(db: Session, daily_record_id: int, data: SalesItemCreate) -> Optional[SalesItem]:
    # Verify day is open
    record = db.query(DailyRecord).filter(DailyRecord.id == daily_record_id).first()
    if not record or record.status != DayStatus.OPEN:
        return None

    # Get product with its variants
    product = (
        db.query(Product)
        .options(joinedload(Product.variants))
        .filter(Product.id == data.product_id)
        .first()
    )
    if not product or not product.is_active:
        return None

    # Get the price from the default variant, or the first active variant
    # Products now have variants, and price is on the variant (price_pln)
    unit_price = None
    for variant in product.variants:
        if variant.is_active:
            if variant.is_default:
                unit_price = variant.price_pln
                break
            elif unit_price is None:
                unit_price = variant.price_pln

    if unit_price is None:
        # No active variant found
        return None

    total_price = unit_price * data.quantity_sold

    db_sale = SalesItem(
        daily_record_id=daily_record_id,
        product_id=data.product_id,
        quantity_sold=data.quantity_sold,
        unit_price=unit_price,
        total_price=total_price,
    )
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    return db_sale


def delete_sale(db: Session, sale_id: int) -> bool:
    sale = db.query(SalesItem).filter(SalesItem.id == sale_id).first()
    if not sale:
        return False

    # Check if day is still open
    record = db.query(DailyRecord).filter(DailyRecord.id == sale.daily_record_id).first()
    if not record or record.status != DayStatus.OPEN:
        return False

    db.delete(sale)
    db.commit()
    return True
