"""
Daily Operations Service

Handles core daily operations:
- Opening a day with inventory counts
- Closing a day with inventory counts and usage calculation
- Getting day summaries
- Pre-filling from previous closing
- Editing closed days

Business Rules:
- Only one day can be open at a time
- Usage = Opening + Deliveries + Transfers - Spoilage - Closing
- All quantities use the unified quantity field (decimal)
- Error messages in Polish
"""

import math
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional
from datetime import date, datetime
from decimal import Decimal

from app.models.daily_record import DailyRecord, DayStatus
from app.models.inventory_snapshot import InventorySnapshot, SnapshotType, InventoryLocation
from app.models.ingredient import Ingredient
from app.models.delivery import Delivery
from app.models.storage_transfer import StorageTransfer
from app.models.spoilage import Spoilage
from app.models.product import ProductVariant, ProductIngredient
from app.models.calculated_sale import CalculatedSale

logger = logging.getLogger(__name__)

from app.schemas.daily_operations import (
    OpenDayRequest,
    OpenDayResponse,
    PreviousDayWarning,
    CloseDayRequest,
    CloseDayResponse,
    UsageItem,
    UsageItemResponse,
    InventorySnapshotItem,
    InventorySnapshotResponse,
    DaySummaryResponse,
    DaySummaryInternalResponse,
    DailyRecordSummary,
    DayEventsSummary,
    DiscrepancyAlert,
    MidDayEventsSummary,
    DeliverySummaryItem,
    TransferSummaryItem,
    SpoilageSummaryItem,
    PreviousClosingResponse,
    PreviousClosingItem,
    EditClosedDayRequest,
    EditClosedDayResponse,
    DailyRecordDetailResponse,
    CalculatedSaleItem,
    PreviousDayStatusResponse,
)


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def _build_snapshot_response(snapshot: InventorySnapshot) -> InventorySnapshotResponse:
    """Convert InventorySnapshot model to response schema."""
    return InventorySnapshotResponse(
        id=snapshot.id,
        daily_record_id=snapshot.daily_record_id,
        ingredient_id=snapshot.ingredient_id,
        ingredient_name=snapshot.ingredient.name,
        unit_label=snapshot.ingredient.unit_label or "szt",
        snapshot_type=snapshot.snapshot_type,
        location=snapshot.location,
        quantity=Decimal(str(snapshot.quantity)),
        recorded_at=snapshot.recorded_at,
    )


def _build_delivery_summary(delivery: Delivery) -> DeliverySummaryItem:
    """Convert Delivery model to summary item."""
    return DeliverySummaryItem(
        id=delivery.id,
        ingredient_id=delivery.ingredient_id,
        ingredient_name=delivery.ingredient.name,
        unit_label=delivery.ingredient.unit_label or "szt",
        quantity=Decimal(str(delivery.quantity)),
        price_pln=Decimal(str(delivery.price_pln)),
        delivered_at=delivery.delivered_at,
    )


def _build_transfer_summary(transfer: StorageTransfer) -> TransferSummaryItem:
    """Convert StorageTransfer model to summary item."""
    return TransferSummaryItem(
        id=transfer.id,
        ingredient_id=transfer.ingredient_id,
        ingredient_name=transfer.ingredient.name,
        unit_label=transfer.ingredient.unit_label or "szt",
        quantity=Decimal(str(transfer.quantity)),
        transferred_at=transfer.transferred_at,
    )


def _build_spoilage_summary(spoilage: Spoilage) -> SpoilageSummaryItem:
    """Convert Spoilage model to summary item."""
    return SpoilageSummaryItem(
        id=spoilage.id,
        ingredient_id=spoilage.ingredient_id,
        ingredient_name=spoilage.ingredient.name,
        unit_label=spoilage.ingredient.unit_label or "szt",
        quantity=Decimal(str(spoilage.quantity)),
        reason=spoilage.reason.value,
        notes=spoilage.notes,
        recorded_at=spoilage.recorded_at,
    )


def _get_mid_day_events_summary(db: Session, daily_record_id: int) -> MidDayEventsSummary:
    """Get summary of all mid-day events for a record."""
    # Get deliveries
    deliveries = db.query(Delivery).filter(
        Delivery.daily_record_id == daily_record_id
    ).all()

    delivery_items = [_build_delivery_summary(d) for d in deliveries]
    deliveries_total = sum(d.price_pln for d in delivery_items)

    # Get transfers
    transfers = db.query(StorageTransfer).filter(
        StorageTransfer.daily_record_id == daily_record_id
    ).all()

    transfer_items = [_build_transfer_summary(t) for t in transfers]

    # Get spoilages
    spoilages = db.query(Spoilage).filter(
        Spoilage.daily_record_id == daily_record_id
    ).all()

    spoilage_items = [_build_spoilage_summary(s) for s in spoilages]

    return MidDayEventsSummary(
        deliveries=delivery_items,
        deliveries_count=len(delivery_items),
        deliveries_total_pln=deliveries_total,
        transfers=transfer_items,
        transfers_count=len(transfer_items),
        spoilages=spoilage_items,
        spoilages_count=len(spoilage_items),
    )


def _get_ingredient_quantities_for_day(
    db: Session,
    daily_record_id: int,
    ingredient_id: int
) -> tuple[Decimal, Decimal, Decimal]:
    """
    Get total deliveries, transfers, and spoilage for an ingredient on a day.
    Returns (deliveries_total, transfers_total, spoilage_total).
    """
    # Sum deliveries
    deliveries_sum = db.query(func.coalesce(func.sum(Delivery.quantity), 0)).filter(
        Delivery.daily_record_id == daily_record_id,
        Delivery.ingredient_id == ingredient_id
    ).scalar()

    # Sum transfers
    transfers_sum = db.query(func.coalesce(func.sum(StorageTransfer.quantity), 0)).filter(
        StorageTransfer.daily_record_id == daily_record_id,
        StorageTransfer.ingredient_id == ingredient_id
    ).scalar()

    # Sum spoilage
    spoilage_sum = db.query(func.coalesce(func.sum(Spoilage.quantity), 0)).filter(
        Spoilage.daily_record_id == daily_record_id,
        Spoilage.ingredient_id == ingredient_id
    ).scalar()

    return (
        Decimal(str(deliveries_sum)),
        Decimal(str(transfers_sum)),
        Decimal(str(spoilage_sum))
    )


# -----------------------------------------------------------------------------
# Sales Derivation (Phase 4)
# -----------------------------------------------------------------------------

def calculate_and_save_sales(
    db: Session,
    daily_record_id: int,
    usage_items: list[UsageItem]
) -> Decimal:
    """
    Calculate derived sales from ingredient usage and save CalculatedSale records.

    Business Rules:
    - BR-02: For each product variant with a primary ingredient:
        - raw_quantity = ingredient_usage / recipe_amount
        - quantity_sold = CEILING(raw_quantity)
    - BR-03: revenue = quantity_sold * price_pln
    - Total Daily Income = SUM(all variant revenues)

    Args:
        db: Database session
        daily_record_id: ID of the daily record
        usage_items: List of calculated usage items for ingredients

    Returns:
        Total income for the day (sum of all revenues)
    """
    # Create lookup for usage by ingredient_id
    usage_map: dict[int, Decimal] = {
        item.ingredient_id: item.usage
        for item in usage_items
    }

    # Get all active product variants with a primary ingredient
    variants_with_primary = (
        db.query(ProductVariant)
        .join(ProductIngredient)
        .filter(
            ProductVariant.is_active == True,
            ProductIngredient.is_primary == True
        )
        .all()
    )

    total_income = Decimal("0")

    for variant in variants_with_primary:
        # Find the primary ingredient for this variant
        primary_ingredient = next(
            (pi for pi in variant.ingredients if pi.is_primary),
            None
        )

        if primary_ingredient is None:
            logger.warning(
                f"Wariant produktu {variant.id} ({variant.product.name}) "
                f"nie ma ustawionego glownego skladnika - pomijam"
            )
            continue

        ingredient_id = primary_ingredient.ingredient_id
        recipe_amount = Decimal(str(primary_ingredient.quantity))

        # Skip if recipe amount is zero or negative (avoid division errors)
        if recipe_amount <= 0:
            logger.warning(
                f"Wariant produktu {variant.id} ma nieprawidlowa ilosc skladnika "
                f"w przepisie ({recipe_amount}) - pomijam"
            )
            continue

        # Get usage for this ingredient
        ingredient_usage = usage_map.get(ingredient_id, Decimal("0"))

        # Skip if usage is zero or negative
        if ingredient_usage <= 0:
            continue

        # Calculate derived sales: raw_quantity = usage / recipe_amount
        raw_quantity = ingredient_usage / recipe_amount

        # Round UP (ceiling) - always round up partial sales
        quantity_sold = Decimal(str(math.ceil(float(raw_quantity))))

        # Calculate revenue
        price_pln = Decimal(str(variant.price_pln))
        revenue_pln = quantity_sold * price_pln

        # Create CalculatedSale record
        calc_sale = CalculatedSale(
            daily_record_id=daily_record_id,
            product_variant_id=variant.id,
            quantity_sold=quantity_sold,
            revenue_pln=revenue_pln,
        )
        db.add(calc_sale)

        total_income += revenue_pln

        logger.debug(
            f"Wyliczona sprzedaz: {variant.product.name} "
            f"({variant.name or 'standardowy'}) - {quantity_sold} szt. = {revenue_pln} PLN"
        )

    return total_income


def _delete_calculated_sales(db: Session, daily_record_id: int) -> None:
    """Delete all calculated sales for a daily record."""
    db.query(CalculatedSale).filter(
        CalculatedSale.daily_record_id == daily_record_id
    ).delete()


def _get_calculated_sales_items(
    db: Session,
    daily_record_id: int
) -> list[CalculatedSaleItem]:
    """Get calculated sales as response items."""
    sales = db.query(CalculatedSale).filter(
        CalculatedSale.daily_record_id == daily_record_id
    ).all()

    items = []
    for sale in sales:
        variant = sale.product_variant
        product = variant.product

        items.append(CalculatedSaleItem(
            product_id=product.id,
            product_name=product.name,
            variant_id=variant.id,
            variant_name=variant.name,
            quantity_sold=Decimal(str(sale.quantity_sold)),
            unit_price_pln=Decimal(str(variant.price_pln)),
            revenue_pln=Decimal(str(sale.revenue_pln)),
        ))

    return items


# -----------------------------------------------------------------------------
# Open Day
# -----------------------------------------------------------------------------

def get_open_day(db: Session) -> Optional[DailyRecord]:
    """Get the currently open day, if any."""
    return db.query(DailyRecord).filter(
        DailyRecord.status == DayStatus.OPEN
    ).first()


def get_record_by_date(db: Session, record_date: date) -> Optional[DailyRecord]:
    """Get a daily record by date."""
    return db.query(DailyRecord).filter(
        DailyRecord.date == record_date
    ).first()


def get_previous_unclosed_day(db: Session, target_date: date) -> Optional[DailyRecord]:
    """
    Check if there's an unclosed day before the target date.
    Returns the unclosed record if found.
    """
    return db.query(DailyRecord).filter(
        DailyRecord.date < target_date,
        DailyRecord.status == DayStatus.OPEN
    ).order_by(desc(DailyRecord.date)).first()


def open_day(
    db: Session,
    data: OpenDayRequest,
    force: bool = False
) -> tuple[Optional[OpenDayResponse], Optional[str]]:
    """
    Open a new day with opening inventory counts.

    Args:
        db: Database session
        data: Open day request with date and opening inventory
        force: If True, allow opening even if previous day not closed

    Returns:
        Tuple of (response, error_message). If error_message is not None, operation failed.
    """
    target_date = data.date or date.today()

    # Check if day already exists for this date
    existing = get_record_by_date(db, target_date)
    if existing:
        return None, f"Dzien {target_date} juz istnieje (ID: {existing.id})"

    # Check for currently open day
    open_record = get_open_day(db)
    if open_record and not force:
        return None, f"Inny dzien jest juz otwarty: {open_record.date}. Zamknij go najpierw lub uzyj opcji 'force'."

    # Check for previous unclosed day (warning, not blocking)
    previous_warning = None
    previous_unclosed = get_previous_unclosed_day(db, target_date)
    if previous_unclosed:
        previous_warning = PreviousDayWarning(
            previous_date=previous_unclosed.date,
            previous_record_id=previous_unclosed.id,
            message="Poprzedni dzien nie zostal zamkniety"
        )

    # Create the daily record
    db_record = DailyRecord(
        date=target_date,
        status=DayStatus.OPEN,
        opened_at=datetime.now(),
        notes=data.notes,
    )
    db.add(db_record)
    db.flush()  # Get the ID

    # Create opening inventory snapshots
    opening_snapshots = []
    for item in data.opening_inventory:
        db_snapshot = InventorySnapshot(
            daily_record_id=db_record.id,
            ingredient_id=item.ingredient_id,
            snapshot_type=SnapshotType.OPEN,
            location=InventoryLocation.SHOP,
            quantity=item.quantity,
        )
        db.add(db_snapshot)
        db.flush()

        # Load ingredient relationship for response
        db.refresh(db_snapshot)
        opening_snapshots.append(_build_snapshot_response(db_snapshot))

    db.commit()
    db.refresh(db_record)

    return OpenDayResponse(
        id=db_record.id,
        date=db_record.date,
        status=db_record.status,
        opened_at=db_record.opened_at,
        opening_snapshots=opening_snapshots,
        previous_day_warning=previous_warning,
    ), None


# -----------------------------------------------------------------------------
# Close Day
# -----------------------------------------------------------------------------

def calculate_usage(
    db: Session,
    daily_record_id: int,
    closing_inventory: list[InventorySnapshotItem]
) -> list[UsageItem]:
    """
    Calculate ingredient usage for a day.

    Formula: Usage = Opening + Deliveries + Transfers - Spoilage - Closing

    Args:
        db: Database session
        daily_record_id: ID of the daily record
        closing_inventory: List of closing inventory items

    Returns:
        List of usage items for each ingredient
    """
    usage_items = []

    # Create lookup for closing quantities
    closing_map = {item.ingredient_id: item.quantity for item in closing_inventory}

    # Get opening snapshots
    opening_snapshots = db.query(InventorySnapshot).filter(
        InventorySnapshot.daily_record_id == daily_record_id,
        InventorySnapshot.snapshot_type == SnapshotType.OPEN,
        InventorySnapshot.location == InventoryLocation.SHOP
    ).all()

    for opening_snap in opening_snapshots:
        ingredient = opening_snap.ingredient
        ingredient_id = ingredient.id

        opening_qty = Decimal(str(opening_snap.quantity))
        closing_qty = closing_map.get(ingredient_id, Decimal("0"))

        # Get mid-day quantities
        deliveries, transfers, spoilage = _get_ingredient_quantities_for_day(
            db, daily_record_id, ingredient_id
        )

        # Calculate expected closing (before actual closing count)
        expected = opening_qty + deliveries + transfers - spoilage

        # Calculate usage
        usage = opening_qty + deliveries + transfers - spoilage - closing_qty

        usage_items.append(UsageItem(
            ingredient_id=ingredient_id,
            ingredient_name=ingredient.name,
            unit_label=ingredient.unit_label or "szt",
            opening=opening_qty,
            deliveries=deliveries,
            transfers=transfers,
            spoilage=spoilage,
            closing=closing_qty,
            usage=usage,
            expected=expected,
        ))

    return usage_items


def close_day(
    db: Session,
    record_id: int,
    data: CloseDayRequest
) -> tuple[Optional[CloseDayResponse], Optional[str]]:
    """
    Close an open day with closing inventory counts.

    Args:
        db: Database session
        record_id: ID of the daily record to close
        data: Close day request with closing inventory

    Returns:
        Tuple of (response, error_message). If error_message is not None, operation failed.
    """
    # Get the record
    db_record = db.query(DailyRecord).filter(DailyRecord.id == record_id).first()
    if not db_record:
        return None, "Rekord nie znaleziony"

    if db_record.status == DayStatus.CLOSED:
        return None, "Dzien jest juz zamkniety"

    # Calculate usage before creating closing snapshots
    usage_summary = calculate_usage(db, record_id, data.closing_inventory)

    # Create closing inventory snapshots
    for item in data.closing_inventory:
        db_snapshot = InventorySnapshot(
            daily_record_id=record_id,
            ingredient_id=item.ingredient_id,
            snapshot_type=SnapshotType.CLOSE,
            location=InventoryLocation.SHOP,
            quantity=item.quantity,
        )
        db.add(db_snapshot)

    # Calculate total delivery cost for the day
    total_delivery_cost = db.query(func.coalesce(func.sum(Delivery.price_pln), 0)).filter(
        Delivery.daily_record_id == record_id
    ).scalar()

    # Calculate and save derived sales (Phase 4: BR-02, BR-03)
    total_income = calculate_and_save_sales(db, record_id, usage_summary)

    # Update record
    db_record.status = DayStatus.CLOSED
    db_record.closed_at = datetime.now()
    db_record.total_delivery_cost_pln = Decimal(str(total_delivery_cost))
    db_record.total_income_pln = total_income
    if data.notes:
        db_record.notes = data.notes

    db.commit()
    db.refresh(db_record)

    return CloseDayResponse(
        id=db_record.id,
        date=db_record.date,
        status=db_record.status,
        opened_at=db_record.opened_at,
        closed_at=db_record.closed_at,
        notes=db_record.notes,
        usage_summary=usage_summary,
    ), None


# -----------------------------------------------------------------------------
# Day Summary
# -----------------------------------------------------------------------------

def _calculate_discrepancy_level(discrepancy_percent: Optional[Decimal]) -> Optional[str]:
    """Determine discrepancy level based on percentage threshold."""
    if discrepancy_percent is None:
        return None
    abs_percent = abs(discrepancy_percent)
    if abs_percent <= 5:
        return "ok"
    elif abs_percent <= 10:
        return "warning"
    else:
        return "critical"


def _build_usage_item_response(
    usage_item: UsageItem,
    ingredient: Ingredient
) -> UsageItemResponse:
    """Convert internal UsageItem to frontend-compatible UsageItemResponse."""
    # Calculate expected_usage (same as usage for closed days)
    expected_usage = usage_item.usage

    # Calculate discrepancy
    discrepancy = None
    discrepancy_percent = None
    if usage_item.closing is not None and usage_item.expected != Decimal("0"):
        discrepancy = usage_item.expected - usage_item.closing
        discrepancy_percent = (discrepancy / usage_item.expected) * 100

    discrepancy_level = _calculate_discrepancy_level(discrepancy_percent)

    return UsageItemResponse(
        ingredient_id=usage_item.ingredient_id,
        ingredient_name=usage_item.ingredient_name,
        unit_type=ingredient.unit_type.value if ingredient.unit_type else "weight",
        unit_label=usage_item.unit_label,
        opening_quantity=usage_item.opening,
        deliveries_quantity=usage_item.deliveries,
        transfers_quantity=usage_item.transfers,
        spoilage_quantity=usage_item.spoilage,
        expected_closing=usage_item.expected,
        closing_quantity=usage_item.closing,
        usage=usage_item.usage,
        expected_usage=expected_usage,
        discrepancy=discrepancy,
        discrepancy_percent=discrepancy_percent,
        discrepancy_level=discrepancy_level,
    )


def _build_discrepancy_alerts(usage_items: list[UsageItemResponse]) -> list[DiscrepancyAlert]:
    """Build discrepancy alerts from usage items."""
    alerts = []
    for item in usage_items:
        if item.discrepancy_level and item.discrepancy_level != "ok":
            message = f"Roznica {item.discrepancy_percent:.1f}% dla {item.ingredient_name}"
            alerts.append(DiscrepancyAlert(
                ingredient_id=item.ingredient_id,
                ingredient_name=item.ingredient_name,
                discrepancy_percent=item.discrepancy_percent or Decimal("0"),
                level=item.discrepancy_level,
                message=message,
            ))
    return alerts


def get_day_summary(db: Session, record_id: int) -> Optional[DaySummaryResponse]:
    """
    Get full summary of a day's operations.

    Returns data in format matching frontend DaySummaryResponse type.
    Includes daily record, events summary, usage calculations, and alerts.
    """
    db_record = db.query(DailyRecord).filter(DailyRecord.id == record_id).first()
    if not db_record:
        return None

    # Get mid-day events
    mid_day_events = _get_mid_day_events_summary(db, record_id)

    # Build events summary for frontend
    events = DayEventsSummary(
        deliveries_count=mid_day_events.deliveries_count,
        deliveries_total_pln=mid_day_events.deliveries_total_pln,
        transfers_count=mid_day_events.transfers_count,
        spoilage_count=mid_day_events.spoilages_count,
    )

    # Calculate usage if day is closed
    usage_items: list[UsageItemResponse] = []
    if db_record.status == DayStatus.CLOSED:
        # Get closing snapshots
        closing_snapshots = db.query(InventorySnapshot).filter(
            InventorySnapshot.daily_record_id == record_id,
            InventorySnapshot.snapshot_type == SnapshotType.CLOSE,
            InventorySnapshot.location == InventoryLocation.SHOP
        ).all()

        if closing_snapshots:
            closing_items = [
                InventorySnapshotItem(
                    ingredient_id=s.ingredient_id,
                    quantity=Decimal(str(s.quantity))
                )
                for s in closing_snapshots
            ]
            internal_usage = calculate_usage(db, record_id, closing_items)

            # Get ingredient lookup for unit_type
            ingredient_ids = [item.ingredient_id for item in internal_usage]
            ingredients = db.query(Ingredient).filter(
                Ingredient.id.in_(ingredient_ids)
            ).all()
            ingredient_map = {ing.id: ing for ing in ingredients}

            # Convert to frontend format
            for item in internal_usage:
                ingredient = ingredient_map.get(item.ingredient_id)
                if ingredient:
                    usage_items.append(_build_usage_item_response(item, ingredient))

    # Build discrepancy alerts
    discrepancy_alerts = _build_discrepancy_alerts(usage_items)

    # Get calculated sales (Phase 4)
    calculated_sales: list[CalculatedSaleItem] = []
    if db_record.status == DayStatus.CLOSED:
        calculated_sales = _get_calculated_sales_items(db, record_id)

    # Build daily record summary
    daily_record_summary = DailyRecordSummary(
        id=db_record.id,
        date=db_record.date,
        status=db_record.status,
        opened_at=db_record.opened_at,
        closed_at=db_record.closed_at,
        notes=db_record.notes,
        total_income_pln=db_record.total_income_pln,
        total_delivery_cost_pln=db_record.total_delivery_cost_pln,
        total_spoilage_cost_pln=db_record.total_spoilage_cost_pln,
        created_at=db_record.created_at,
        updated_at=db_record.updated_at,
    )

    # Format times as ISO strings for frontend Date parsing
    opening_time = db_record.opened_at.isoformat() if db_record.opened_at else None
    closing_time = db_record.closed_at.isoformat() if db_record.closed_at else None

    return DaySummaryResponse(
        daily_record=daily_record_summary,
        opening_time=opening_time,
        closing_time=closing_time,
        events=events,
        usage_items=usage_items,
        calculated_sales=calculated_sales,
        total_income_pln=db_record.total_income_pln or Decimal("0"),
        discrepancy_alerts=discrepancy_alerts,
    )


# -----------------------------------------------------------------------------
# Previous Closing (for pre-fill)
# -----------------------------------------------------------------------------

def get_previous_closing(db: Session) -> PreviousClosingResponse:
    """
    Get the previous day's closing inventory for pre-filling opening counts.

    Returns closing snapshots from the most recent closed day.
    """
    # Find the most recent closed day
    last_closed = db.query(DailyRecord).filter(
        DailyRecord.status == DayStatus.CLOSED
    ).order_by(desc(DailyRecord.date)).first()

    if not last_closed:
        # No closed days, return all active ingredients with zero quantities
        ingredients = db.query(Ingredient).filter(Ingredient.is_active == True).all()
        return PreviousClosingResponse(
            message="Brak poprzednich zamknietych dni",
            items=[
                PreviousClosingItem(
                    ingredient_id=ing.id,
                    ingredient_name=ing.name,
                    unit_label=ing.unit_label or "szt",
                    is_active=ing.is_active,
                    quantity=Decimal("0"),
                    closed_date=date.today()
                )
                for ing in ingredients
            ]
        )

    # Get closing snapshots from last closed day
    closing_snapshots = db.query(InventorySnapshot).filter(
        InventorySnapshot.daily_record_id == last_closed.id,
        InventorySnapshot.snapshot_type == SnapshotType.CLOSE,
        InventorySnapshot.location == InventoryLocation.SHOP
    ).all()

    # Create lookup of snapshot quantities
    snapshot_map = {s.ingredient_id: Decimal(str(s.quantity)) for s in closing_snapshots}

    # Get all active ingredients
    ingredients = db.query(Ingredient).filter(Ingredient.is_active == True).all()

    items = []
    for ing in ingredients:
        quantity = snapshot_map.get(ing.id, Decimal("0"))
        items.append(PreviousClosingItem(
            ingredient_id=ing.id,
            ingredient_name=ing.name,
            unit_label=ing.unit_label or "szt",
            is_active=ing.is_active,
            quantity=quantity,
            closed_date=last_closed.date
        ))

    return PreviousClosingResponse(
        previous_date=last_closed.date,
        previous_record_id=last_closed.id,
        items=items,
    )


# -----------------------------------------------------------------------------
# Edit Closed Day
# -----------------------------------------------------------------------------

def edit_closed_day(
    db: Session,
    record_id: int,
    data: EditClosedDayRequest
) -> tuple[Optional[EditClosedDayResponse], Optional[str]]:
    """
    Edit a closed day's closing inventory.

    Allows updating closing counts and recalculating usage.

    Args:
        db: Database session
        record_id: ID of the daily record to edit
        data: Edit request with new closing inventory

    Returns:
        Tuple of (response, error_message). If error_message is not None, operation failed.
    """
    db_record = db.query(DailyRecord).filter(DailyRecord.id == record_id).first()
    if not db_record:
        return None, "Rekord nie znaleziony"

    if db_record.status != DayStatus.CLOSED:
        return None, "Mozna edytowac tylko zamkniete dni"

    # Delete existing closing snapshots
    db.query(InventorySnapshot).filter(
        InventorySnapshot.daily_record_id == record_id,
        InventorySnapshot.snapshot_type == SnapshotType.CLOSE,
        InventorySnapshot.location == InventoryLocation.SHOP
    ).delete()

    # Delete existing calculated sales (Phase 4)
    _delete_calculated_sales(db, record_id)

    # Create new closing snapshots
    for item in data.closing_inventory:
        db_snapshot = InventorySnapshot(
            daily_record_id=record_id,
            ingredient_id=item.ingredient_id,
            snapshot_type=SnapshotType.CLOSE,
            location=InventoryLocation.SHOP,
            quantity=item.quantity,
        )
        db.add(db_snapshot)

    # Update notes if provided
    if data.notes is not None:
        db_record.notes = data.notes

    # Recalculate usage
    usage_summary = calculate_usage(db, record_id, data.closing_inventory)

    # Recalculate and save derived sales (Phase 4)
    total_income = calculate_and_save_sales(db, record_id, usage_summary)
    db_record.total_income_pln = total_income

    db.commit()
    db.refresh(db_record)

    return EditClosedDayResponse(
        id=db_record.id,
        date=db_record.date,
        status=db_record.status,
        updated_at=db_record.updated_at,
        usage_summary=usage_summary,
        message="Dzien zostal zaktualizowany"
    ), None


# -----------------------------------------------------------------------------
# Get Daily Record Detail
# -----------------------------------------------------------------------------

def get_daily_record_detail(db: Session, record_id: int) -> Optional[DailyRecordDetailResponse]:
    """
    Get detailed information about a daily record.

    Includes all snapshots and mid-day events.
    """
    db_record = db.query(DailyRecord).filter(DailyRecord.id == record_id).first()
    if not db_record:
        return None

    # Get opening snapshots
    opening_snapshots = db.query(InventorySnapshot).filter(
        InventorySnapshot.daily_record_id == record_id,
        InventorySnapshot.snapshot_type == SnapshotType.OPEN,
        InventorySnapshot.location == InventoryLocation.SHOP
    ).all()
    opening_responses = [_build_snapshot_response(s) for s in opening_snapshots]

    # Get closing snapshots
    closing_snapshots = db.query(InventorySnapshot).filter(
        InventorySnapshot.daily_record_id == record_id,
        InventorySnapshot.snapshot_type == SnapshotType.CLOSE,
        InventorySnapshot.location == InventoryLocation.SHOP
    ).all()
    closing_responses = [_build_snapshot_response(s) for s in closing_snapshots]

    # Get mid-day events
    mid_day_events = _get_mid_day_events_summary(db, record_id)

    return DailyRecordDetailResponse(
        id=db_record.id,
        date=db_record.date,
        status=db_record.status,
        opened_at=db_record.opened_at,
        closed_at=db_record.closed_at,
        notes=db_record.notes,
        total_income_pln=db_record.total_income_pln,
        total_delivery_cost_pln=Decimal(str(db_record.total_delivery_cost_pln or 0)),
        total_spoilage_cost_pln=Decimal(str(db_record.total_spoilage_cost_pln or 0)),
        created_at=db_record.created_at,
        updated_at=db_record.updated_at,
        opening_snapshots=opening_responses,
        closing_snapshots=closing_responses,
        mid_day_events=mid_day_events,
    )


# -----------------------------------------------------------------------------
# Get Today's Record
# -----------------------------------------------------------------------------

def get_today_record(db: Session) -> Optional[DailyRecord]:
    """Get today's daily record if it exists."""
    today = date.today()
    return db.query(DailyRecord).filter(DailyRecord.date == today).first()


def get_recent_records(db: Session, limit: int = 7) -> list[dict]:
    """
    Get recent daily records for history display.

    Returns simplified records with alerts count for dashboard/history views.
    """
    records = db.query(DailyRecord).order_by(
        desc(DailyRecord.date)
    ).limit(limit).all()

    result = []
    for record in records:
        # Count discrepancy alerts for closed days
        alerts_count = 0
        if record.status == DayStatus.CLOSED:
            # Get usage items and count warnings/criticals
            closing_snapshots = db.query(InventorySnapshot).filter(
                InventorySnapshot.daily_record_id == record.id,
                InventorySnapshot.snapshot_type == SnapshotType.CLOSE,
                InventorySnapshot.location == InventoryLocation.SHOP
            ).all()

            if closing_snapshots:
                closing_items = [
                    InventorySnapshotItem(
                        ingredient_id=s.ingredient_id,
                        quantity=Decimal(str(s.quantity))
                    )
                    for s in closing_snapshots
                ]
                usage_items = calculate_usage(db, record.id, closing_items)

                # Get ingredient lookup
                ingredient_ids = [item.ingredient_id for item in usage_items]
                ingredients = db.query(Ingredient).filter(
                    Ingredient.id.in_(ingredient_ids)
                ).all()
                ingredient_map = {ing.id: ing for ing in ingredients}

                for item in usage_items:
                    ingredient = ingredient_map.get(item.ingredient_id)
                    if ingredient:
                        response_item = _build_usage_item_response(item, ingredient)
                        if response_item.discrepancy_level in ("warning", "critical"):
                            alerts_count += 1

        result.append({
            "id": record.id,
            "date": record.date.isoformat(),
            "status": record.status.value,
            "total_income_pln": float(record.total_income_pln) if record.total_income_pln else None,
            "alerts_count": alerts_count,
            "opened_at": record.opened_at.isoformat() if record.opened_at else None,
            "closed_at": record.closed_at.isoformat() if record.closed_at else None,
        })

    return result


# -----------------------------------------------------------------------------
# Check Previous Day Status
# -----------------------------------------------------------------------------

def check_previous_day_status(db: Session) -> PreviousDayStatusResponse:
    """
    Check if there is a previous unclosed day that needs to be closed.

    VR-06: Warning if previous day not closed.

    Returns information about any unclosed previous day.
    """
    today = date.today()

    # Find any unclosed day before today
    unclosed = get_previous_unclosed_day(db, today)

    if unclosed:
        return PreviousDayStatusResponse(
            has_unclosed_previous=True,
            unclosed_date=unclosed.date,
            unclosed_record_id=unclosed.id,
            message=f"Dzien {unclosed.date} nie zostal zamkniety"
        )

    return PreviousDayStatusResponse(
        has_unclosed_previous=False,
        message="Wszystkie poprzednie dni sa zamkniete"
    )
