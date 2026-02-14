"""
Day Wizard Service

Provides wizard-style flow for daily operations:
- Opening step: confirm shifts and enter opening inventory
- Mid-day step: track deliveries, transfers, spoilage
- Closing step: enter closing inventory and preview sales

Business Rules:
- Opening step requires at least one shift assignment
- Opening step requires at least one inventory entry
- Usage = Opening + Deliveries + Transfers - Spoilage - Closing
- Discrepancy thresholds: OK (<=5%), Warning (5-10%), Critical (>10%)
"""

import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import date
from decimal import Decimal

from app.models.daily_record import DailyRecord, DayStatus
from app.models.inventory_snapshot import InventorySnapshot, SnapshotType, InventoryLocation
from app.models.ingredient import Ingredient
from app.models.delivery import Delivery, DeliveryItem
from app.models.storage_transfer import StorageTransfer
from app.models.spoilage import Spoilage
from app.models.shift_assignment import ShiftAssignment
from app.models.employee import Employee
from app.models.position import Position

from app.schemas.day_wizard import (
    WizardStep,
    WizardStateResponse,
    OpeningStepState,
    MidDayStepState,
    ClosingStepState,
    CompleteOpeningRequest,
    CompleteOpeningResponse,
    SuggestedShift,
    SuggestedShiftsResponse,
    IngredientUsage,
    CalculatedSale,
    SalesPreviewSummary,
    SalesPreviewResponse,
    DiscrepancyLevel,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Exception Classes
# =============================================================================


class DailyRecordNotFoundError(Exception):
    """Raised when a daily record is not found."""
    def __init__(self, record_id: int):
        self.record_id = record_id
        super().__init__(f"Rekord dzienny o ID {record_id} nie zostal znaleziony")


class DayNotOpenError(Exception):
    """Raised when trying to modify a closed day."""
    def __init__(self, record_id: int):
        self.record_id = record_id
        super().__init__(f"Dzien o ID {record_id} nie jest otwarty")


class OpeningNotCompletedError(Exception):
    """Raised when opening step is not completed."""
    def __init__(self, record_id: int):
        self.record_id = record_id
        super().__init__(f"Etap otwarcia dla dnia o ID {record_id} nie zostal zakonczony")


class InventoryNotEnteredError(Exception):
    """Raised when inventory has not been entered."""
    def __init__(self):
        super().__init__("Nie wprowadzono stanow magazynowych")


class WizardStepNotFoundError(Exception):
    """Raised when wizard step cannot be determined."""
    def __init__(self, record_id: int):
        self.record_id = record_id
        super().__init__(f"Nie mozna okreslic kroku kreatora dla dnia o ID {record_id}")


# =============================================================================
# Discrepancy Thresholds (Module-level constants)
# =============================================================================

DISCREPANCY_OK_THRESHOLD = Decimal("5")      # <= 5% is OK
DISCREPANCY_WARNING_THRESHOLD = Decimal("10")  # 5-10% is Warning
# > 10% is Critical


# =============================================================================
# Helper Functions
# =============================================================================


def _calculate_discrepancy_level(percent: Optional[Decimal]) -> DiscrepancyLevel:
    """Determine discrepancy level based on percentage threshold."""
    if percent is None:
        return DiscrepancyLevel.OK

    abs_percent = abs(percent)
    if abs_percent <= DISCREPANCY_OK_THRESHOLD:
        return DiscrepancyLevel.OK
    elif abs_percent <= DISCREPANCY_WARNING_THRESHOLD:
        return DiscrepancyLevel.WARNING
    else:
        return DiscrepancyLevel.CRITICAL


def _get_ingredient_quantities_for_day(
    db: Session,
    daily_record_id: int,
    ingredient_id: int
) -> tuple[Decimal, Decimal, Decimal]:
    """
    Get total deliveries, transfers, and spoilage for an ingredient on a day.
    Returns (deliveries_total, transfers_total, spoilage_total).
    """
    # Sum deliveries (join through DeliveryItem since deliveries have multi-item structure)
    deliveries_sum = db.query(func.coalesce(func.sum(DeliveryItem.quantity), 0)).join(
        Delivery, DeliveryItem.delivery_id == Delivery.id
    ).filter(
        Delivery.daily_record_id == daily_record_id,
        DeliveryItem.ingredient_id == ingredient_id
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


# =============================================================================
# Day Wizard Service Class
# =============================================================================


class DayWizardService:
    """
    Service for wizard-style daily operations.

    Provides methods for:
    - Getting current wizard state
    - Completing opening step
    - Calculating sales preview
    - Getting suggested shifts
    """

    def __init__(self, db: Session):
        self.db = db

    def _get_daily_record(self, record_id: int) -> DailyRecord:
        """Get daily record or raise DailyRecordNotFoundError."""
        record = self.db.query(DailyRecord).filter(
            DailyRecord.id == record_id
        ).first()

        if not record:
            raise DailyRecordNotFoundError(record_id)

        return record

    def _get_opening_state(self, record_id: int) -> OpeningStepState:
        """Get the state of the opening step."""
        # Check for opening inventory snapshots
        opening_count = self.db.query(func.count(InventorySnapshot.id)).filter(
            InventorySnapshot.daily_record_id == record_id,
            InventorySnapshot.snapshot_type == SnapshotType.OPEN,
            InventorySnapshot.location == InventoryLocation.SHOP
        ).scalar()

        inventory_entered = opening_count > 0

        # Check for shift assignments
        shift_count = self.db.query(func.count(ShiftAssignment.id)).filter(
            ShiftAssignment.daily_record_id == record_id
        ).scalar()

        shifts_confirmed = shift_count > 0

        # Opening is completed if both inventory and shifts are entered
        completed = inventory_entered and shifts_confirmed

        return OpeningStepState(
            completed=completed,
            inventory_entered=inventory_entered,
            shifts_confirmed=shifts_confirmed,
            shift_count=shift_count,
        )

    def _get_mid_day_state(self, record_id: int) -> MidDayStepState:
        """Get the state of the mid-day step."""
        # Count deliveries (via DeliveryItem)
        deliveries_count = self.db.query(func.count(DeliveryItem.id)).join(
            Delivery, DeliveryItem.delivery_id == Delivery.id
        ).filter(
            Delivery.daily_record_id == record_id
        ).scalar()

        # Total delivery cost
        total_delivery_cost = self.db.query(
            func.coalesce(func.sum(Delivery.total_cost_pln), 0)
        ).filter(
            Delivery.daily_record_id == record_id
        ).scalar()

        # Count transfers
        transfers_count = self.db.query(func.count(StorageTransfer.id)).filter(
            StorageTransfer.daily_record_id == record_id
        ).scalar()

        # Count spoilage
        spoilage_count = self.db.query(func.count(Spoilage.id)).filter(
            Spoilage.daily_record_id == record_id
        ).scalar()

        return MidDayStepState(
            deliveries_count=deliveries_count,
            transfers_count=transfers_count,
            spoilage_count=spoilage_count,
            total_delivery_cost_pln=Decimal(str(total_delivery_cost)),
        )

    def _get_closing_state(self, record_id: int) -> ClosingStepState:
        """Get the state of the closing step."""
        # Check for closing inventory snapshots
        closing_count = self.db.query(func.count(InventorySnapshot.id)).filter(
            InventorySnapshot.daily_record_id == record_id,
            InventorySnapshot.snapshot_type == SnapshotType.CLOSE,
            InventorySnapshot.location == InventoryLocation.SHOP
        ).scalar()

        closing_inventory_entered = closing_count > 0

        # For now, we don't have discrepancy counts until closing is entered
        # These will be calculated during close
        return ClosingStepState(
            closing_inventory_entered=closing_inventory_entered,
            has_discrepancies=False,
            critical_discrepancy_count=0,
            warning_discrepancy_count=0,
        )

    def _determine_current_step(
        self,
        record: DailyRecord,
        opening_state: OpeningStepState,
        closing_state: Optional[ClosingStepState] = None
    ) -> Optional[WizardStep]:
        """Determine the current wizard step based on day state."""
        if record.status == DayStatus.CLOSED:
            return WizardStep.COMPLETED

        # If opening not completed, we're in opening step
        if not opening_state.completed:
            return WizardStep.OPENING

        # If closing inventory has been entered, we're in closing step
        if closing_state and closing_state.closing_inventory_entered:
            return WizardStep.CLOSING

        # Opening is complete, we're in mid-day by default
        return WizardStep.MID_DAY

    def get_wizard_state(self, record_id: int) -> WizardStateResponse:
        """
        Get the current wizard state for a daily record.

        Args:
            record_id: ID of the daily record

        Returns:
            WizardStateResponse with current step and states

        Raises:
            DailyRecordNotFoundError: If record doesn't exist
        """
        record = self._get_daily_record(record_id)

        opening_state = self._get_opening_state(record_id)
        mid_day_state = self._get_mid_day_state(record_id)
        closing_state = self._get_closing_state(record_id)

        current_step = self._determine_current_step(record, opening_state, closing_state)

        return WizardStateResponse(
            daily_record_id=record.id,
            date=record.date,
            status=record.status,
            current_step=current_step,
            opening=opening_state,
            mid_day=mid_day_state,
            closing=closing_state,
            opened_at=record.opened_at,
            notes=record.notes,
        )

    def advance_to_closing(self, record_id: int) -> None:
        """
        Advance wizard to closing step.

        This marks the day as entering the closing phase by creating
        placeholder closing snapshots. The wizard state will return
        CLOSING step after this is called.

        Args:
            record_id: ID of the daily record

        Raises:
            DailyRecordNotFoundError: If record doesn't exist
            DayNotOpenError: If day is already closed
            OpeningNotCompletedError: If opening step is not completed
        """
        record = self._get_daily_record(record_id)

        if record.status != DayStatus.OPEN:
            raise DayNotOpenError(record_id)

        # Validate that opening is complete
        opening_state = self._get_opening_state(record_id)
        if not opening_state.completed:
            raise OpeningNotCompletedError(record_id)

        # Check if closing snapshots already exist
        closing_count = self.db.query(func.count(InventorySnapshot.id)).filter(
            InventorySnapshot.daily_record_id == record_id,
            InventorySnapshot.snapshot_type == SnapshotType.CLOSE,
            InventorySnapshot.location == InventoryLocation.SHOP
        ).scalar()

        if closing_count > 0:
            # Already in closing step
            return

        # Create placeholder closing snapshots for all opening ingredients
        opening_snapshots = self.db.query(InventorySnapshot).filter(
            InventorySnapshot.daily_record_id == record_id,
            InventorySnapshot.snapshot_type == SnapshotType.OPEN,
            InventorySnapshot.location == InventoryLocation.SHOP
        ).all()

        for opening_snap in opening_snapshots:
            closing_snap = InventorySnapshot(
                daily_record_id=record_id,
                ingredient_id=opening_snap.ingredient_id,
                snapshot_type=SnapshotType.CLOSE,
                location=InventoryLocation.SHOP,
                quantity=Decimal("0"),  # Placeholder value
            )
            self.db.add(closing_snap)

        self.db.commit()

    def complete_opening(
        self,
        record_id: int,
        request: CompleteOpeningRequest
    ) -> CompleteOpeningResponse:
        """
        Complete the opening step with shifts and inventory.

        Args:
            record_id: ID of the daily record
            request: Opening data with shifts and inventory

        Returns:
            CompleteOpeningResponse with updated state

        Raises:
            DailyRecordNotFoundError: If record doesn't exist
            DayNotOpenError: If day is closed
            ValueError: If no shifts provided
            InventoryNotEnteredError: If no inventory provided
        """
        record = self._get_daily_record(record_id)

        if record.status != DayStatus.OPEN:
            raise DayNotOpenError(record_id)

        # Validate shifts
        if not request.confirmed_shifts:
            raise ValueError("Wymagany jest co najmniej jeden pracownik na zmianie")

        # Validate inventory
        if not request.opening_inventory:
            raise InventoryNotEnteredError()

        # Clear existing shift assignments for this day (if re-completing)
        self.db.query(ShiftAssignment).filter(
            ShiftAssignment.daily_record_id == record_id
        ).delete()

        # Clear existing opening snapshots (if re-completing)
        self.db.query(InventorySnapshot).filter(
            InventorySnapshot.daily_record_id == record_id,
            InventorySnapshot.snapshot_type == SnapshotType.OPEN,
            InventorySnapshot.location == InventoryLocation.SHOP
        ).delete()

        # Create shift assignments
        for shift in request.confirmed_shifts:
            db_shift = ShiftAssignment(
                daily_record_id=record_id,
                employee_id=shift.employee_id,
                start_time=shift.start_time,
                end_time=shift.end_time,
            )
            self.db.add(db_shift)

        # Create opening inventory snapshots
        for item in request.opening_inventory:
            db_snapshot = InventorySnapshot(
                daily_record_id=record_id,
                ingredient_id=item.ingredient_id,
                snapshot_type=SnapshotType.OPEN,
                location=item.location,
                quantity=item.quantity,
            )
            self.db.add(db_snapshot)

        self.db.commit()

        # Get updated state
        opening_state = self._get_opening_state(record_id)

        return CompleteOpeningResponse(
            daily_record_id=record_id,
            current_step=WizardStep.MID_DAY,
            opening=opening_state,
            message="Otwarcie dnia zakonczone pomyslnie",
        )

    def get_suggested_shifts(
        self,
        daily_record_id: int,
        target_date: date
    ) -> list[SuggestedShift]:
        """
        Get suggested shifts for a day based on templates.

        Args:
            daily_record_id: ID of the daily record
            target_date: Date to get suggestions for

        Returns:
            List of suggested shifts (empty if no templates)

        Raises:
            DailyRecordNotFoundError: If record doesn't exist
        """
        # Verify record exists
        self._get_daily_record(daily_record_id)

        # Try to import ShiftTemplate - if it doesn't exist, return empty list
        try:
            from app.models.shift_template import ShiftTemplate

            # Get day of week (0=Monday, 6=Sunday)
            day_of_week = target_date.weekday()

            # Query shift templates for this day
            templates = self.db.query(ShiftTemplate).filter(
                ShiftTemplate.day_of_week == day_of_week
            ).all()

            suggestions = []
            for template in templates:
                employee = self.db.query(Employee).filter(
                    Employee.id == template.employee_id
                ).first()

                if employee and employee.is_active:
                    position = self.db.query(Position).filter(
                        Position.id == employee.position_id
                    ).first()

                    suggestions.append(SuggestedShift(
                        employee_id=employee.id,
                        employee_name=employee.name,
                        position_name=position.name if position else "",
                        start_time=template.start_time,
                        end_time=template.end_time,
                        source="template",
                    ))

            return suggestions

        except ImportError:
            # ShiftTemplate model doesn't exist yet, return empty list
            return []

    def calculate_sales_preview(
        self,
        daily_record_id: int,
        closing_inventory: dict[int, Decimal]
    ) -> dict:
        """
        Calculate sales preview based on closing inventory.

        Formula: Used = Opening + Deliveries + Transfers - Spoilage - Closing

        Args:
            daily_record_id: ID of the daily record
            closing_inventory: Dict mapping ingredient_id to closing quantity

        Returns:
            Dict with ingredients_used, calculated_sales, summary, warnings

        Raises:
            DailyRecordNotFoundError: If record doesn't exist
        """
        record = self._get_daily_record(daily_record_id)

        # Get opening snapshots
        opening_snapshots = self.db.query(InventorySnapshot).filter(
            InventorySnapshot.daily_record_id == daily_record_id,
            InventorySnapshot.snapshot_type == SnapshotType.OPEN,
            InventorySnapshot.location == InventoryLocation.SHOP
        ).all()

        if not opening_snapshots:
            return {
                "ingredients_used": [],
                "calculated_sales": [],
                "summary": {
                    "total_revenue_pln": Decimal("0"),
                    "total_delivery_cost_pln": Decimal("0"),
                    "gross_profit_pln": Decimal("0"),
                },
                "warnings": [],
            }

        ingredients_used = []
        warnings = []

        # Get ingredient lookup
        ingredient_ids = [s.ingredient_id for s in opening_snapshots]
        ingredients = self.db.query(Ingredient).filter(
            Ingredient.id.in_(ingredient_ids)
        ).all()
        ingredient_map = {ing.id: ing for ing in ingredients}

        for opening_snap in opening_snapshots:
            ingredient = ingredient_map.get(opening_snap.ingredient_id)
            if not ingredient:
                continue

            ingredient_id = opening_snap.ingredient_id
            opening_qty = Decimal(str(opening_snap.quantity))

            # Get closing quantity from input
            closing_qty = closing_inventory.get(ingredient_id)

            # Get mid-day quantities
            deliveries, transfers, spoilage = _get_ingredient_quantities_for_day(
                self.db, daily_record_id, ingredient_id
            )

            # Calculate expected closing (before actual count)
            expected = opening_qty + deliveries + transfers - spoilage

            if closing_qty is None:
                # No closing entered for this ingredient, skip calculation
                ingredients_used.append({
                    "ingredient_id": ingredient_id,
                    "ingredient_name": ingredient.name,
                    "unit_type": ingredient.unit_type.value if ingredient.unit_type else "weight",
                    "unit_label": ingredient.unit_label or "szt",
                    "opening": opening_qty,
                    "deliveries": deliveries,
                    "transfers": transfers,
                    "spoilage": spoilage,
                    "closing": None,
                    "expected": expected,
                    "used": None,
                    "discrepancy_percent": None,
                    "discrepancy_level": None,
                })
                continue

            # Calculate usage
            used = opening_qty + deliveries + transfers - spoilage - closing_qty

            # Calculate discrepancy
            discrepancy_percent = None
            discrepancy_level = DiscrepancyLevel.OK

            if expected != Decimal("0"):
                # Discrepancy = difference between expected and actual closing
                actual_diff = expected - closing_qty
                discrepancy_percent = (actual_diff / expected) * 100
                discrepancy_level = _calculate_discrepancy_level(discrepancy_percent)

            # Add warnings for negative usage (more closing than expected)
            if used < Decimal("0"):
                warnings.append(
                    f"Discrepancy detected for {ingredient.name}: "
                    f"closing ({closing_qty}) > expected ({expected})"
                )

            # Add warnings for high discrepancy
            if discrepancy_level == DiscrepancyLevel.CRITICAL:
                warnings.append(
                    f"Critical discrepancy for {ingredient.name}: "
                    f"{abs(discrepancy_percent):.1f}%"
                )

            ingredients_used.append({
                "ingredient_id": ingredient_id,
                "ingredient_name": ingredient.name,
                "unit_type": ingredient.unit_type.value if ingredient.unit_type else "weight",
                "unit_label": ingredient.unit_label or "szt",
                "opening": opening_qty,
                "deliveries": deliveries,
                "transfers": transfers,
                "spoilage": spoilage,
                "closing": closing_qty,
                "expected": expected,
                "used": used,
                "discrepancy_percent": discrepancy_percent,
                "discrepancy_level": discrepancy_level.value if discrepancy_level else None,
            })

        # Calculate total delivery cost
        total_delivery_cost = self.db.query(
            func.coalesce(func.sum(Delivery.total_cost_pln), 0)
        ).filter(
            Delivery.daily_record_id == daily_record_id
        ).scalar()

        # For now, calculated_sales is empty (would need product recipe matching)
        # This would be implemented similar to calculate_and_save_sales in daily_operations_service

        return {
            "ingredients_used": ingredients_used,
            "calculated_sales": [],
            "summary": {
                "total_revenue_pln": Decimal("0"),
                "total_delivery_cost_pln": Decimal(str(total_delivery_cost)),
                "gross_profit_pln": Decimal("0") - Decimal(str(total_delivery_cost)),
            },
            "warnings": warnings,
        }
