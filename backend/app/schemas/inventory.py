"""
Inventory schemas for snapshot operations.

Supports both legacy (quantity_grams/quantity_count) and new unified (quantity) fields
for backwards compatibility during transition period.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.models.inventory_snapshot import SnapshotType, InventoryLocation


class InventorySnapshotCreate(BaseModel):
    """
    Create schema for inventory snapshot.

    Supports both legacy fields (quantity_grams, quantity_count) and new unified field (quantity).
    If quantity is provided, it takes precedence.
    """
    ingredient_id: int
    quantity_grams: Optional[Decimal] = None  # Legacy: for weight-based ingredients
    quantity_count: Optional[int] = None      # Legacy: for count-based ingredients
    quantity: Optional[Decimal] = None        # New unified field
    location: InventoryLocation = InventoryLocation.SHOP

    @model_validator(mode="after")
    def validate_quantity(self):
        """Ensure at least one quantity is provided."""
        if self.quantity is None and self.quantity_grams is None and self.quantity_count is None:
            raise ValueError("Wymagana jest ilosc (quantity, quantity_grams lub quantity_count)")
        return self

    def get_unified_quantity(self) -> Decimal:
        """Get the quantity value, preferring unified field."""
        if self.quantity is not None:
            return self.quantity
        if self.quantity_grams is not None:
            return self.quantity_grams
        if self.quantity_count is not None:
            return Decimal(str(self.quantity_count))
        return Decimal("0")


class InventorySnapshotResponse(BaseModel):
    """Response schema for inventory snapshot."""
    id: int
    daily_record_id: int
    ingredient_id: int
    ingredient_name: Optional[str] = None
    snapshot_type: SnapshotType
    location: InventoryLocation = InventoryLocation.SHOP
    quantity: Decimal  # Unified quantity field
    quantity_grams: Optional[Decimal] = None  # Legacy, for backwards compatibility
    quantity_count: Optional[int] = None       # Legacy, for backwards compatibility
    recorded_at: datetime

    class Config:
        from_attributes = True


class InventoryDiscrepancy(BaseModel):
    """
    Discrepancy between expected and actual ingredient usage.

    Used for alerting when actual usage differs significantly from expected
    based on recorded sales.
    """
    ingredient_id: int
    ingredient_name: str
    unit_type: str
    unit_label: str = "szt"  # Display label (kg, szt, etc.)
    opening_quantity: Decimal
    closing_quantity: Decimal
    deliveries: Decimal = Decimal("0")      # Deliveries during the day
    transfers: Decimal = Decimal("0")       # Storage transfers during the day
    spoilage: Decimal = Decimal("0")        # Spoilage during the day
    actual_used: Decimal                    # Opening + Deliveries + Transfers - Spoilage - Closing
    expected_used: Decimal                  # Based on sales * recipe amounts
    discrepancy: Decimal                    # actual_used - expected_used
    discrepancy_percent: Optional[Decimal] = None  # As percentage of expected
    alert_level: str = "ok"                 # "ok", "warning", "critical"


class CurrentStock(BaseModel):
    """Current stock level for an ingredient."""
    ingredient_id: int
    ingredient_name: str
    unit_type: str
    unit_label: str = "szt"
    current_stock: Decimal


class IngredientAvailability(BaseModel):
    """
    Availability status for an ingredient on a given day.

    Shows opening stock and what's available after mid-day events.
    """
    ingredient_id: int
    ingredient_name: str
    unit_label: str
    opening: Decimal
    deliveries: Decimal
    transfers: Decimal
    spoilage: Decimal
    available: Decimal  # Opening + Deliveries + Transfers - Spoilage


class TransferStockItem(BaseModel):
    """
    Stock information for an ingredient, showing both storage and shop quantities.
    Used in TransferModal to help users decide how much to transfer.
    """
    ingredient_id: int
    ingredient_name: str
    unit_type: str
    unit_label: str
    storage_quantity: Decimal  # Current quantity in storage
    shop_quantity: Decimal     # Current quantity in shop (opening + deliveries + transfers - spoilage)
