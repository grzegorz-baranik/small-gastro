from pydantic import BaseModel
from decimal import Decimal
from typing import List, Optional


class ProductReconciliation(BaseModel):
    product_variant_id: int
    product_name: str
    variant_name: Optional[str]
    recorded_qty: int
    recorded_revenue: Decimal
    calculated_qty: Decimal
    calculated_revenue: Decimal
    qty_difference: Decimal
    revenue_difference: Decimal


class MissingSuggestion(BaseModel):
    product_variant_id: int
    product_name: str
    variant_name: Optional[str]
    suggested_qty: int
    suggested_revenue: Decimal
    reason: str


class ReconciliationReportResponse(BaseModel):
    daily_record_id: int
    recorded_total_pln: Decimal
    calculated_total_pln: Decimal
    discrepancy_pln: Decimal
    discrepancy_percent: float
    has_critical_discrepancy: bool
    has_no_recorded_sales: bool
    by_product: List[ProductReconciliation]
    suggestions: List[MissingSuggestion]
