"""
Reconciliation Service

Compares recorded sales (manually entered) with calculated sales (derived from
ingredient usage) to identify discrepancies and generate suggestions.

Business Rules:
- Recorded sales: manually entered by staff during the day
- Calculated sales: derived from ingredient usage divided by recipe amounts
- Discrepancy = Recorded - Calculated
- Critical threshold: 30% or more discrepancy
- Warning threshold: 10% or more discrepancy
- Suggestions generated when calculated_qty > recorded_qty
"""

import logging
from decimal import Decimal
from typing import Dict, List, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.recorded_sale import RecordedSale
from app.models.calculated_sale import CalculatedSale
from app.models.product import ProductVariant
from app.models.daily_record import DailyRecord
from app.schemas.reconciliation import (
    ProductReconciliation,
    MissingSuggestion,
    ReconciliationReportResponse,
)

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

CRITICAL_THRESHOLD = 30.0  # 30% discrepancy
WARNING_THRESHOLD = 10.0   # 10% discrepancy
MAX_SUGGESTIONS = 5        # Maximum number of suggestions to return


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def _get_recorded_by_product(
    db: Session,
    daily_record_id: int
) -> Dict[int, Tuple[int, Decimal]]:
    """
    Aggregate recorded sales by product_variant_id.

    Args:
        db: Database session
        daily_record_id: ID of the daily record

    Returns:
        Dict mapping variant_id to (total_qty, total_revenue)
        Excludes voided sales.
    """
    # Query recorded sales grouped by product_variant_id
    # Exclude voided sales (voided_at IS NOT NULL)
    results = db.query(
        RecordedSale.product_variant_id,
        func.sum(RecordedSale.quantity).label("total_qty"),
        func.sum(RecordedSale.quantity * RecordedSale.unit_price_pln).label("total_revenue")
    ).filter(
        RecordedSale.daily_record_id == daily_record_id,
        RecordedSale.voided_at.is_(None)  # Exclude voided sales
    ).group_by(
        RecordedSale.product_variant_id
    ).all()

    recorded_map: Dict[int, Tuple[int, Decimal]] = {}
    for variant_id, total_qty, total_revenue in results:
        recorded_map[variant_id] = (
            int(total_qty) if total_qty else 0,
            Decimal(str(total_revenue)) if total_revenue else Decimal("0")
        )

    return recorded_map


def _get_calculated_by_product(
    db: Session,
    daily_record_id: int
) -> Dict[int, Tuple[Decimal, Decimal]]:
    """
    Query CalculatedSale table for a daily record.

    Args:
        db: Database session
        daily_record_id: ID of the daily record

    Returns:
        Dict mapping variant_id to (quantity_sold, revenue_pln)
    """
    results = db.query(
        CalculatedSale.product_variant_id,
        CalculatedSale.quantity_sold,
        CalculatedSale.revenue_pln
    ).filter(
        CalculatedSale.daily_record_id == daily_record_id
    ).all()

    calculated_map: Dict[int, Tuple[Decimal, Decimal]] = {}
    for variant_id, quantity_sold, revenue_pln in results:
        calculated_map[variant_id] = (
            Decimal(str(quantity_sold)) if quantity_sold else Decimal("0"),
            Decimal(str(revenue_pln)) if revenue_pln else Decimal("0")
        )

    return calculated_map


def _merge_comparisons(
    db: Session,
    recorded: Dict[int, Tuple[int, Decimal]],
    calculated: Dict[int, Tuple[Decimal, Decimal]]
) -> List[ProductReconciliation]:
    """
    Merge recorded and calculated sales for comparison.

    Args:
        db: Database session
        recorded: Dict mapping variant_id to (total_qty, total_revenue)
        calculated: Dict mapping variant_id to (quantity_sold, revenue_pln)

    Returns:
        List of ProductReconciliation sorted by revenue_difference DESC
    """
    # Union all variant IDs from both sources
    all_variant_ids = set(recorded.keys()) | set(calculated.keys())

    if not all_variant_ids:
        return []

    # Get variant information in a single query
    variants = db.query(ProductVariant).filter(
        ProductVariant.id.in_(all_variant_ids)
    ).all()
    variant_map = {v.id: v for v in variants}

    comparisons: List[ProductReconciliation] = []

    for variant_id in all_variant_ids:
        # Get recorded data (defaults to 0 if not present)
        rec_qty, rec_revenue = recorded.get(variant_id, (0, Decimal("0")))

        # Get calculated data (defaults to 0 if not present)
        calc_qty, calc_revenue = calculated.get(variant_id, (Decimal("0"), Decimal("0")))

        # Get variant details
        variant = variant_map.get(variant_id)
        if variant:
            product_name = variant.product.name
            variant_name = variant.name
        else:
            product_name = f"Nieznany produkt (ID: {variant_id})"
            variant_name = None

        # Calculate differences
        qty_difference = Decimal(str(rec_qty)) - calc_qty
        revenue_difference = rec_revenue - calc_revenue

        comparisons.append(ProductReconciliation(
            product_variant_id=variant_id,
            product_name=product_name,
            variant_name=variant_name,
            recorded_qty=rec_qty,
            recorded_revenue=rec_revenue,
            calculated_qty=calc_qty,
            calculated_revenue=calc_revenue,
            qty_difference=qty_difference,
            revenue_difference=revenue_difference,
        ))

    # Sort by revenue_difference DESC (biggest discrepancies first)
    comparisons.sort(key=lambda x: x.revenue_difference, reverse=True)

    return comparisons


def _generate_suggestions(
    by_product: List[ProductReconciliation]
) -> List[MissingSuggestion]:
    """
    Generate suggestions for missing sales.

    For products where calculated_qty > recorded_qty, suggest adding
    the difference.

    Args:
        by_product: List of ProductReconciliation items

    Returns:
        List of MissingSuggestion, limited to top MAX_SUGGESTIONS items
    """
    suggestions: List[MissingSuggestion] = []

    for item in by_product:
        # Only suggest when calculated > recorded (negative qty_difference)
        if item.qty_difference < 0:
            suggested_qty = int(abs(item.qty_difference))

            if suggested_qty <= 0:
                continue

            # Calculate suggested revenue based on unit price
            if item.recorded_qty > 0:
                unit_price = item.recorded_revenue / Decimal(str(item.recorded_qty))
            elif item.calculated_qty > 0:
                unit_price = item.calculated_revenue / item.calculated_qty
            else:
                unit_price = Decimal("0")

            suggested_revenue = unit_price * Decimal(str(suggested_qty))

            suggestions.append(MissingSuggestion(
                product_variant_id=item.product_variant_id,
                product_name=item.product_name,
                variant_name=item.variant_name,
                suggested_qty=suggested_qty,
                suggested_revenue=suggested_revenue,
                reason=f"Zuzycie skladnikow sugeruje {suggested_qty} wiecej",
            ))

    # Sort by suggested_revenue DESC and limit to MAX_SUGGESTIONS
    suggestions.sort(key=lambda x: x.suggested_revenue, reverse=True)

    return suggestions[:MAX_SUGGESTIONS]


# -----------------------------------------------------------------------------
# Main Reconciliation Function
# -----------------------------------------------------------------------------

def reconcile(
    db: Session,
    daily_record_id: int
) -> ReconciliationReportResponse:
    """
    Generate a reconciliation report comparing recorded vs calculated sales.

    Args:
        db: Database session
        daily_record_id: ID of the daily record to reconcile

    Returns:
        ReconciliationReportResponse with:
        - Overall totals and discrepancy percentage
        - Product-by-product comparison
        - Suggestions for missing sales
    """
    logger.info(f"Generowanie raportu uzgodnienia dla dnia ID: {daily_record_id}")

    # Get recorded sales by product
    recorded = _get_recorded_by_product(db, daily_record_id)
    logger.debug(f"Znaleziono {len(recorded)} produktow z zarejestrowana sprzedaza")

    # Get calculated sales by product
    calculated = _get_calculated_by_product(db, daily_record_id)
    logger.debug(f"Znaleziono {len(calculated)} produktow z obliczona sprzedaza")

    # Merge and compare
    by_product = _merge_comparisons(db, recorded, calculated)

    # Calculate totals
    recorded_total_pln = sum(
        item.recorded_revenue for item in by_product
    )
    calculated_total_pln = sum(
        item.calculated_revenue for item in by_product
    )
    discrepancy_pln = recorded_total_pln - calculated_total_pln

    # Calculate discrepancy percentage (avoid division by zero)
    if calculated_total_pln > 0:
        discrepancy_percent = float(
            (discrepancy_pln / calculated_total_pln) * Decimal("100")
        )
    elif recorded_total_pln > 0:
        # If no calculated sales but recorded sales exist, 100% discrepancy
        discrepancy_percent = 100.0
    else:
        discrepancy_percent = 0.0

    # Determine if critical discrepancy exists
    abs_discrepancy_percent = abs(discrepancy_percent)
    has_critical_discrepancy = abs_discrepancy_percent >= CRITICAL_THRESHOLD

    # Check if there are no recorded sales at all
    has_no_recorded_sales = all(item.recorded_qty == 0 for item in by_product)

    # Generate suggestions
    suggestions = _generate_suggestions(by_product)

    logger.info(
        f"Raport uzgodnienia: zapisane={recorded_total_pln} PLN, "
        f"obliczone={calculated_total_pln} PLN, "
        f"roznica={discrepancy_percent:.1f}%"
    )

    return ReconciliationReportResponse(
        daily_record_id=daily_record_id,
        recorded_total_pln=recorded_total_pln,
        calculated_total_pln=calculated_total_pln,
        discrepancy_pln=discrepancy_pln,
        discrepancy_percent=discrepancy_percent,
        has_critical_discrepancy=has_critical_discrepancy,
        has_no_recorded_sales=has_no_recorded_sales,
        by_product=by_product,
        suggestions=suggestions,
    )
