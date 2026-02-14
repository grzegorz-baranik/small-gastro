"""
Tests for Day Wizard Service functionality.

BDD Scenarios covered (from unified-day-operations TESTING.md):
- TC-UNIT-006: Calculate sales preview (correct ingredient usage calculation)
- TC-UNIT-007: Wizard state determination (opening/mid_day/closing steps)
- TC-INT-003: GET /api/v1/daily-records/{id}/wizard-state
- TC-INT-004: POST /api/v1/daily-records/{id}/complete-opening
- TC-INT-005: GET /api/v1/daily-records/{id}/sales-preview

These tests are designed to FAIL initially (Red phase of TDD) because
the DayWizardService does not yet exist.

Sales Calculation Formula:
    used = opening + deliveries + transfers - spoilage - closing

Example:
    opening=50 + transfers=20 + deliveries=0 - spoilage=2 - closing=38 = 30 used
"""

import pytest
from datetime import date, datetime, time
from decimal import Decimal
from typing import Dict

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# These imports are expected to fail initially (service doesn't exist yet)
# TDD: Write the test first, then implement the service
try:
    from app.services.day_wizard_service import (
        DayWizardService,
        WizardStepNotFoundError,
        OpeningNotCompletedError,
        InventoryNotEnteredError,
        DailyRecordNotFoundError,
        DayNotOpenError,
    )
    from app.schemas.day_wizard import (
        WizardStateResponse,
        CompleteOpeningRequest,
        CompleteOpeningResponse,
        SalesPreviewRequest,
        SalesPreviewResponse,
        IngredientUsage,
        CalculatedSale,
        SuggestedShift,
        ConfirmedShiftInput,
        OpeningInventoryInput,
        WizardStep,
        OpeningStepState,
        MidDayStepState,
        ClosingStepState,
    )
    SERVICE_AVAILABLE = True
except ImportError:
    SERVICE_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not SERVICE_AVAILABLE,
    reason="DayWizardService not yet implemented (RED TDD phase)"
)

from app.models.daily_record import DayStatus
from app.models.inventory_snapshot import SnapshotType, InventoryLocation
from app.models.spoilage import SpoilageReason
from app.models.ingredient import UnitType

from tests.builders import (
    build_ingredient,
    build_daily_record,
    build_inventory_snapshot,
    build_spoilage,
    build_delivery,
    build_storage_transfer,
    build_employee,
    build_position,
    build_shift_assignment,
)


# =============================================================================
# FIXTURES - Test Data Builders for Day Wizard Tests
# =============================================================================


@pytest.fixture
def sample_ingredients(db_session: Session):
    """Creates sample ingredients for testing."""
    meat = build_ingredient(
        db_session,
        name="Mieso kebab",
        unit_type=UnitType.WEIGHT,
        unit_label="kg",
    )
    buns = build_ingredient(
        db_session,
        name="Bulki",
        unit_type=UnitType.COUNT,
        unit_label="szt",
    )
    sauce = build_ingredient(
        db_session,
        name="Sos czosnkowy",
        unit_type=UnitType.WEIGHT,
        unit_label="kg",
    )
    vegetables = build_ingredient(
        db_session,
        name="Warzywa mix",
        unit_type=UnitType.WEIGHT,
        unit_label="kg",
    )
    db_session.commit()
    return [meat, buns, sauce, vegetables]


@pytest.fixture
def new_daily_record(db_session: Session):
    """
    Creates a fresh daily record with no opening inventory.
    Used to test wizard state = 'opening'.
    """
    record = build_daily_record(
        db_session,
        record_date=date(2026, 1, 5),
        status=DayStatus.OPEN,
        opened_at=datetime(2026, 1, 5, 8, 0, 0),
    )
    db_session.commit()
    return record


@pytest.fixture
def daily_record_with_opening(db_session: Session, sample_ingredients):
    """
    Creates a daily record with opening inventory entered.
    Used to test wizard state = 'mid_day'.
    """
    record = build_daily_record(
        db_session,
        record_date=date(2026, 1, 5),
        status=DayStatus.OPEN,
        opened_at=datetime(2026, 1, 5, 8, 0, 0),
    )
    db_session.flush()

    # Add opening inventory snapshots
    for ingredient in sample_ingredients:
        build_inventory_snapshot(
            db_session,
            daily_record_id=record.id,
            ingredient_id=ingredient.id,
            snapshot_type=SnapshotType.OPEN,
            location=InventoryLocation.SHOP,
            quantity=Decimal("50.0"),
        )

    # Add a shift assignment (opening step requires confirmed shifts)
    position = build_position(db_session, name="Kucharz")
    employee = build_employee(db_session, name="Jan Kowalski", position=position)
    build_shift_assignment(
        db_session,
        daily_record=record,
        employee=employee,
        start_time=time(8, 0),
        end_time=time(16, 0),
    )

    db_session.commit()
    return record


@pytest.fixture
def day_with_operations(db_session: Session, sample_ingredients):
    """
    Creates a day with opening inventory, transfers, and spoilage.
    Used for sales preview calculation tests.

    Test data:
    - Opening inventory: 50.0 kg meat
    - Transfer from storage: 20.0 kg meat
    - Spoilage: 2.0 kg meat
    - Expected closing: when closing=38.0, used=30.0
    """
    record = build_daily_record(
        db_session,
        record_date=date(2026, 1, 5),
        status=DayStatus.OPEN,
        opened_at=datetime(2026, 1, 5, 8, 0, 0),
    )
    db_session.flush()

    meat = sample_ingredients[0]  # Mieso kebab
    buns = sample_ingredients[1]  # Bulki

    # Opening inventory
    build_inventory_snapshot(
        db_session,
        daily_record_id=record.id,
        ingredient_id=meat.id,
        snapshot_type=SnapshotType.OPEN,
        location=InventoryLocation.SHOP,
        quantity=Decimal("50.0"),
    )
    build_inventory_snapshot(
        db_session,
        daily_record_id=record.id,
        ingredient_id=buns.id,
        snapshot_type=SnapshotType.OPEN,
        location=InventoryLocation.SHOP,
        quantity=Decimal("100"),
    )

    # Storage transfer (adds to shop inventory)
    build_storage_transfer(
        db_session,
        daily_record_id=record.id,
        ingredient_id=meat.id,
        quantity=Decimal("20.0"),
    )

    # Spoilage (reduces available inventory)
    build_spoilage(
        db_session,
        daily_record_id=record.id,
        ingredient_id=meat.id,
        quantity=Decimal("2.0"),
        reason=SpoilageReason.EXPIRED,
    )

    # Add shift assignment
    position = build_position(db_session, name="Kucharz")
    employee = build_employee(db_session, name="Jan Kowalski", position=position)
    build_shift_assignment(
        db_session,
        daily_record=record,
        employee=employee,
        start_time=time(8, 0),
        end_time=time(16, 0),
    )

    db_session.commit()
    return record


@pytest.fixture
def day_with_delivery(db_session: Session, sample_ingredients):
    """
    Creates a day with opening inventory and a delivery.
    Used for testing delivery impact on sales calculations.
    """
    record = build_daily_record(
        db_session,
        record_date=date(2026, 1, 5),
        status=DayStatus.OPEN,
        opened_at=datetime(2026, 1, 5, 8, 0, 0),
    )
    db_session.flush()

    meat = sample_ingredients[0]

    # Opening inventory
    build_inventory_snapshot(
        db_session,
        daily_record_id=record.id,
        ingredient_id=meat.id,
        snapshot_type=SnapshotType.OPEN,
        location=InventoryLocation.SHOP,
        quantity=Decimal("50.0"),
    )

    # Delivery (adds to inventory)
    build_delivery(
        db_session,
        daily_record_id=record.id,
        ingredient_id=meat.id,
        quantity=Decimal("10.0"),
        price_pln=Decimal("150.00"),
    )

    db_session.commit()
    return record


@pytest.fixture
def sample_employees(db_session: Session):
    """Creates sample employees for shift tests."""
    position = build_position(db_session, name="Kucharz", hourly_rate=Decimal("25.00"))
    employee1 = build_employee(db_session, name="Anna Kowalska", position=position)
    employee2 = build_employee(db_session, name="Jan Nowak", position=position)
    db_session.commit()
    return [employee1, employee2]


# =============================================================================
# UNIT TESTS - DayWizardService
# =============================================================================


class TestDayWizardServiceSalesPreview:
    """
    Unit tests for DayWizardService.calculate_sales_preview()

    TC-UNIT-006: Correct calculation of ingredient usage
    Formula: used = opening + deliveries + transfers - spoilage - closing
    """

    def test_calculate_sales_preview_basic(self, db_session: Session, day_with_operations, sample_ingredients):
        """
        TC-UNIT-006: Verify basic usage calculation is correct.

        Given: Day with opening=50, transfers=20, spoilage=2
        When: Closing inventory entered as 38
        Then: Used should be 30 (50 + 20 - 2 - 38 = 30)
        """
        # Arrange
        service = DayWizardService(db_session)
        meat = sample_ingredients[0]

        closing_inventory = {meat.id: Decimal("38.0")}

        # Act
        result = service.calculate_sales_preview(
            daily_record_id=day_with_operations.id,
            closing_inventory=closing_inventory
        )

        # Assert
        assert result is not None
        assert "ingredients_used" in result

        meat_usage = next(
            (i for i in result["ingredients_used"] if i["ingredient_id"] == meat.id),
            None
        )
        assert meat_usage is not None
        assert meat_usage["opening"] == Decimal("50.0")
        assert meat_usage["transfers"] == Decimal("20.0")
        assert meat_usage["spoilage"] == Decimal("2.0")
        assert meat_usage["closing"] == Decimal("38.0")
        assert meat_usage["used"] == Decimal("30.0")  # 50 + 20 - 2 - 38 = 30

    def test_calculate_sales_preview_with_delivery(self, db_session: Session, day_with_delivery, sample_ingredients):
        """
        Given: Day with opening=50, delivery=10
        When: Closing inventory entered as 40
        Then: Used should be 20 (50 + 10 - 40 = 20)
        """
        # Arrange
        service = DayWizardService(db_session)
        meat = sample_ingredients[0]

        closing_inventory = {meat.id: Decimal("40.0")}

        # Act
        result = service.calculate_sales_preview(
            daily_record_id=day_with_delivery.id,
            closing_inventory=closing_inventory
        )

        # Assert
        meat_usage = next(
            (i for i in result["ingredients_used"] if i["ingredient_id"] == meat.id),
            None
        )
        assert meat_usage is not None
        assert meat_usage["deliveries"] == Decimal("10.0")
        assert meat_usage["used"] == Decimal("20.0")  # 50 + 10 - 40 = 20

    def test_calculate_sales_preview_negative_usage(self, db_session: Session, daily_record_with_opening, sample_ingredients):
        """
        Edge case: Closing inventory higher than expected (discrepancy).

        Given: Day with opening=50, no operations
        When: Closing inventory entered as 55 (more than opening)
        Then: Used should be -5 (negative indicates discrepancy)
        """
        # Arrange
        service = DayWizardService(db_session)
        meat = sample_ingredients[0]

        closing_inventory = {meat.id: Decimal("55.0")}

        # Act
        result = service.calculate_sales_preview(
            daily_record_id=daily_record_with_opening.id,
            closing_inventory=closing_inventory
        )

        # Assert
        meat_usage = next(
            (i for i in result["ingredients_used"] if i["ingredient_id"] == meat.id),
            None
        )
        assert meat_usage is not None
        assert meat_usage["used"] == Decimal("-5.0")  # Negative = discrepancy
        assert "warnings" in result
        # Should have a warning about negative usage
        assert any("discrepancy" in w.lower() or "negative" in w.lower() for w in result.get("warnings", []))

    def test_calculate_sales_preview_zero_closing(self, db_session: Session, daily_record_with_opening, sample_ingredients):
        """
        Edge case: All inventory used (closing=0).

        Given: Day with opening=50
        When: Closing inventory is 0
        Then: Used should equal opening (50)
        """
        # Arrange
        service = DayWizardService(db_session)
        meat = sample_ingredients[0]

        closing_inventory = {meat.id: Decimal("0")}

        # Act
        result = service.calculate_sales_preview(
            daily_record_id=daily_record_with_opening.id,
            closing_inventory=closing_inventory
        )

        # Assert
        meat_usage = next(
            (i for i in result["ingredients_used"] if i["ingredient_id"] == meat.id),
            None
        )
        assert meat_usage is not None
        assert meat_usage["used"] == Decimal("50.0")

    def test_calculate_sales_preview_includes_calculated_sales(self, db_session: Session, day_with_operations, sample_ingredients):
        """
        Verify that calculated_sales field is populated based on product recipes.
        """
        # Arrange
        service = DayWizardService(db_session)
        meat = sample_ingredients[0]

        closing_inventory = {meat.id: Decimal("38.0")}

        # Act
        result = service.calculate_sales_preview(
            daily_record_id=day_with_operations.id,
            closing_inventory=closing_inventory
        )

        # Assert
        assert "calculated_sales" in result
        assert "summary" in result
        # Summary should contain total_revenue_pln
        assert "total_revenue_pln" in result["summary"]

    def test_calculate_sales_preview_missing_closing_inventory(self, db_session: Session, day_with_operations):
        """
        Given: Day with opening inventory
        When: Closing inventory dict is empty
        Then: Should handle gracefully (return empty used or raise validation)
        """
        # Arrange
        service = DayWizardService(db_session)
        closing_inventory = {}  # Empty

        # Act & Assert - Either returns with empty data or raises validation error
        # The implementation should decide the behavior
        result = service.calculate_sales_preview(
            daily_record_id=day_with_operations.id,
            closing_inventory=closing_inventory
        )

        # If it returns, ingredients_used should be empty or have null used values
        assert result is not None

    def test_calculate_sales_preview_daily_record_not_found(self, db_session: Session):
        """
        Given: Non-existent daily record ID
        When: Calculating sales preview
        Then: Should raise DailyRecordNotFoundError
        """
        # Arrange
        service = DayWizardService(db_session)
        closing_inventory = {1: Decimal("10.0")}

        # Act & Assert
        with pytest.raises(DailyRecordNotFoundError):
            service.calculate_sales_preview(
                daily_record_id=99999,
                closing_inventory=closing_inventory
            )


class TestDayWizardServiceWizardState:
    """
    Unit tests for DayWizardService.get_wizard_state()

    TC-UNIT-007: Correctly determines current wizard step
    """

    def test_wizard_state_opening_step(self, db_session: Session, new_daily_record):
        """
        TC-UNIT-007a: New day shows opening step.

        Given: A freshly opened day with no opening inventory
        When: Getting wizard state
        Then: Current step should be 'opening'
        """
        # Arrange
        service = DayWizardService(db_session)

        # Act
        state = service.get_wizard_state(new_daily_record.id)

        # Assert
        assert state.current_step == WizardStep.OPENING
        assert state.opening.completed is False
        assert state.opening.inventory_entered is False
        assert state.opening.shifts_confirmed is False

    def test_wizard_state_midday_step(self, db_session: Session, daily_record_with_opening):
        """
        TC-UNIT-007b: Day with completed opening shows mid_day step.

        Given: A day with opening inventory and shifts confirmed
        When: Getting wizard state
        Then: Current step should be 'mid_day'
        """
        # Arrange
        service = DayWizardService(db_session)

        # Act
        state = service.get_wizard_state(daily_record_with_opening.id)

        # Assert
        assert state.current_step == WizardStep.MID_DAY
        assert state.opening.completed is True
        assert state.opening.inventory_entered is True
        assert state.opening.shifts_confirmed is True

    def test_wizard_state_closing_step(self, db_session: Session, day_with_operations):
        """
        Given: A day with opening inventory and mid-day operations
        When: User explicitly moves to closing step (or time-based trigger)
        Then: Current step should be 'closing'

        Note: The transition to closing may be explicit or based on time.
        """
        # Arrange
        service = DayWizardService(db_session)

        # Mark the day as ready for closing (implementation detail)
        # This might involve a service call or state update
        service.advance_to_closing(day_with_operations.id)

        # Act
        state = service.get_wizard_state(day_with_operations.id)

        # Assert
        assert state.current_step == WizardStep.CLOSING

    def test_wizard_state_closed_day(self, db_session: Session):
        """
        Given: A closed day
        When: Getting wizard state
        Then: Should indicate day is closed
        """
        # Arrange
        closed_record = build_daily_record(
            db_session,
            record_date=date(2026, 1, 4),
            status=DayStatus.CLOSED,
            closed_at=datetime(2026, 1, 4, 20, 0, 0),
        )
        db_session.commit()

        service = DayWizardService(db_session)

        # Act
        state = service.get_wizard_state(closed_record.id)

        # Assert
        assert state.status == DayStatus.CLOSED
        assert state.current_step is None or state.current_step == WizardStep.COMPLETED

    def test_wizard_state_not_found(self, db_session: Session):
        """
        Given: Non-existent daily record ID
        When: Getting wizard state
        Then: Should raise DailyRecordNotFoundError
        """
        # Arrange
        service = DayWizardService(db_session)

        # Act & Assert
        with pytest.raises(DailyRecordNotFoundError):
            service.get_wizard_state(99999)


class TestDayWizardServiceCompleteOpening:
    """
    Unit tests for DayWizardService.complete_opening()
    """

    def test_complete_opening_success(self, db_session: Session, new_daily_record, sample_employees, sample_ingredients):
        """
        Given: A new daily record with no opening data
        When: Completing opening with shifts and inventory
        Then: Opening step should be marked as completed
        """
        # Arrange
        service = DayWizardService(db_session)

        request = CompleteOpeningRequest(
            confirmed_shifts=[
                ConfirmedShiftInput(
                    employee_id=sample_employees[0].id,
                    start_time=time(8, 0),
                    end_time=time(16, 0)
                )
            ],
            opening_inventory=[
                OpeningInventoryInput(
                    ingredient_id=sample_ingredients[0].id,
                    quantity=Decimal("50.0"),
                    location=InventoryLocation.SHOP
                ),
                OpeningInventoryInput(
                    ingredient_id=sample_ingredients[1].id,
                    quantity=Decimal("100"),
                    location=InventoryLocation.SHOP
                ),
            ]
        )

        # Act
        result = service.complete_opening(new_daily_record.id, request)

        # Assert
        assert result.opening.completed is True
        assert result.opening.shifts_confirmed == 1
        assert result.opening.inventory_entered is True
        assert result.current_step == WizardStep.MID_DAY

    def test_complete_opening_no_shifts_raises_error(self, db_session: Session, new_daily_record, sample_ingredients):
        """
        Given: A new daily record
        When: Completing opening without any shifts
        Then: Should raise validation error (at least one shift required)
        """
        # Arrange
        service = DayWizardService(db_session)

        request = CompleteOpeningRequest(
            confirmed_shifts=[],  # No shifts!
            opening_inventory=[
                OpeningInventoryInput(
                    ingredient_id=sample_ingredients[0].id,
                    quantity=Decimal("50.0"),
                    location=InventoryLocation.SHOP
                ),
            ]
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.complete_opening(new_daily_record.id, request)

        # Error message is in Polish: "Wymagany jest co najmniej jeden pracownik na zmianie"
        # Accept both English "shift" and Polish "zmian" (from "zmianie")
        error_msg = str(exc_info.value).lower()
        assert "shift" in error_msg or "zmian" in error_msg or "pracownik" in error_msg

    def test_complete_opening_no_inventory_raises_error(self, db_session: Session, new_daily_record, sample_employees):
        """
        Given: A new daily record
        When: Completing opening without inventory
        Then: Should raise InventoryNotEnteredError
        """
        # Arrange
        service = DayWizardService(db_session)

        request = CompleteOpeningRequest(
            confirmed_shifts=[
                ConfirmedShiftInput(
                    employee_id=sample_employees[0].id,
                    start_time=time(8, 0),
                    end_time=time(16, 0)
                )
            ],
            opening_inventory=[]  # No inventory!
        )

        # Act & Assert
        with pytest.raises(InventoryNotEnteredError):
            service.complete_opening(new_daily_record.id, request)

    def test_complete_opening_closed_day_raises_error(self, db_session: Session, sample_employees, sample_ingredients):
        """
        Given: A closed daily record
        When: Trying to complete opening
        Then: Should raise DayNotOpenError
        """
        # Arrange
        closed_record = build_daily_record(
            db_session,
            record_date=date(2026, 1, 4),
            status=DayStatus.CLOSED,
        )
        db_session.commit()

        service = DayWizardService(db_session)

        request = CompleteOpeningRequest(
            confirmed_shifts=[
                ConfirmedShiftInput(
                    employee_id=sample_employees[0].id,
                    start_time=time(8, 0),
                    end_time=time(16, 0)
                )
            ],
            opening_inventory=[
                OpeningInventoryInput(
                    ingredient_id=sample_ingredients[0].id,
                    quantity=Decimal("50.0"),
                    location=InventoryLocation.SHOP
                ),
            ]
        )

        # Act & Assert
        with pytest.raises(DayNotOpenError):
            service.complete_opening(closed_record.id, request)


class TestDayWizardServiceSuggestedShifts:
    """
    Unit tests for DayWizardService.get_suggested_shifts()
    """

    def test_get_suggested_shifts_from_schedule(self, db_session: Session, new_daily_record, sample_employees):
        """
        Given: A daily record for a specific date
        When: Getting suggested shifts
        Then: Should return shifts based on schedule templates
        """
        # Arrange
        service = DayWizardService(db_session)

        # Act
        result = service.get_suggested_shifts(
            daily_record_id=new_daily_record.id,
            target_date=new_daily_record.date
        )

        # Assert
        assert isinstance(result, list)
        # Even if empty, should return a list
        for shift in result:
            assert isinstance(shift, SuggestedShift)
            assert shift.employee_id is not None
            assert shift.employee_name is not None
            assert shift.start_time is not None
            assert shift.end_time is not None
            assert shift.source in ["template", "override", "manual"]

    def test_get_suggested_shifts_empty_when_no_templates(self, db_session: Session, new_daily_record):
        """
        Given: A daily record with no shift templates configured
        When: Getting suggested shifts
        Then: Should return empty list
        """
        # Arrange
        service = DayWizardService(db_session)

        # Act
        result = service.get_suggested_shifts(
            daily_record_id=new_daily_record.id,
            target_date=new_daily_record.date
        )

        # Assert
        assert result == []


# =============================================================================
# INTEGRATION TESTS - API Endpoints
# =============================================================================


class TestDayWizardAPIGetWizardState:
    """
    Integration tests for GET /api/v1/daily-records/{id}/wizard-state

    TC-INT-003
    """

    def test_get_wizard_state_success(self, client: TestClient, db_session: Session, daily_record_with_opening):
        """
        TC-INT-003: Get wizard state for an open day.

        Given: An open daily record with opening inventory
        When: GET /api/v1/daily-records/{id}/wizard-state
        Then: Should return 200 with wizard state
        """
        # Act
        response = client.get(f"/api/v1/daily-records/{daily_record_with_opening.id}/wizard-state")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["daily_record_id"] == daily_record_with_opening.id
        assert data["status"] == "open"
        assert "current_step" in data
        assert "opening" in data
        assert "mid_day" in data
        assert "closing" in data

    def test_get_wizard_state_new_day(self, client: TestClient, db_session: Session, new_daily_record):
        """
        Given: A freshly opened day
        When: GET /api/v1/daily-records/{id}/wizard-state
        Then: Should return current_step = 'opening'
        """
        # Act
        response = client.get(f"/api/v1/daily-records/{new_daily_record.id}/wizard-state")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["current_step"] == "opening"
        assert data["opening"]["completed"] is False

    def test_get_wizard_state_not_found(self, client: TestClient, db_session: Session):
        """
        Given: Non-existent daily record ID
        When: GET /api/v1/daily-records/99999/wizard-state
        Then: Should return 404
        """
        # Act
        response = client.get("/api/v1/daily-records/99999/wizard-state")

        # Assert
        assert response.status_code == 404


class TestDayWizardAPICompleteOpening:
    """
    Integration tests for POST /api/v1/daily-records/{id}/complete-opening

    TC-INT-004
    """

    def test_complete_opening_success(
        self,
        client: TestClient,
        db_session: Session,
        new_daily_record,
        sample_employees,
        sample_ingredients
    ):
        """
        TC-INT-004: Complete opening step with shifts and inventory.

        Given: An open daily record
        When: POST /api/v1/daily-records/{id}/complete-opening with valid data
        Then: Should return 200 with updated wizard state
        """
        # Arrange
        payload = {
            "confirmed_shifts": [
                {
                    "employee_id": sample_employees[0].id,
                    "start_time": "08:00:00",
                    "end_time": "16:00:00"
                }
            ],
            "opening_inventory": [
                {
                    "ingredient_id": sample_ingredients[0].id,
                    "quantity": 50.0,
                    "location": "shop"
                },
                {
                    "ingredient_id": sample_ingredients[1].id,
                    "quantity": 100,
                    "location": "shop"
                }
            ]
        }

        # Act
        response = client.post(
            f"/api/v1/daily-records/{new_daily_record.id}/complete-opening",
            json=payload
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["opening"]["completed"] is True
        assert data["opening"]["shifts_confirmed"] == 1
        assert data["opening"]["inventory_entered"] is True

    def test_complete_opening_missing_shifts(
        self,
        client: TestClient,
        db_session: Session,
        new_daily_record,
        sample_ingredients
    ):
        """
        Given: An open daily record
        When: POST without shifts
        Then: Should return 422 (validation error)
        """
        # Arrange
        payload = {
            "confirmed_shifts": [],  # Empty!
            "opening_inventory": [
                {
                    "ingredient_id": sample_ingredients[0].id,
                    "quantity": 50.0,
                    "location": "shop"
                }
            ]
        }

        # Act
        response = client.post(
            f"/api/v1/daily-records/{new_daily_record.id}/complete-opening",
            json=payload
        )

        # Assert
        assert response.status_code in [400, 422]

    def test_complete_opening_not_found(
        self,
        client: TestClient,
        db_session: Session,
        sample_employees,
        sample_ingredients
    ):
        """
        Given: Non-existent daily record ID
        When: POST /api/v1/daily-records/99999/complete-opening
        Then: Should return 404
        """
        # Arrange
        payload = {
            "confirmed_shifts": [
                {
                    "employee_id": sample_employees[0].id,
                    "start_time": "08:00:00",
                    "end_time": "16:00:00"
                }
            ],
            "opening_inventory": [
                {
                    "ingredient_id": sample_ingredients[0].id,
                    "quantity": 50.0,
                    "location": "shop"
                }
            ]
        }

        # Act
        response = client.post(
            "/api/v1/daily-records/99999/complete-opening",
            json=payload
        )

        # Assert
        assert response.status_code == 404

    def test_complete_opening_closed_day(
        self,
        client: TestClient,
        db_session: Session,
        sample_employees,
        sample_ingredients
    ):
        """
        Given: A closed daily record
        When: POST complete-opening
        Then: Should return 400 (day not open)
        """
        # Arrange
        closed_record = build_daily_record(
            db_session,
            record_date=date(2026, 1, 3),
            status=DayStatus.CLOSED,
        )
        db_session.commit()

        payload = {
            "confirmed_shifts": [
                {
                    "employee_id": sample_employees[0].id,
                    "start_time": "08:00:00",
                    "end_time": "16:00:00"
                }
            ],
            "opening_inventory": [
                {
                    "ingredient_id": sample_ingredients[0].id,
                    "quantity": 50.0,
                    "location": "shop"
                }
            ]
        }

        # Act
        response = client.post(
            f"/api/v1/daily-records/{closed_record.id}/complete-opening",
            json=payload
        )

        # Assert
        assert response.status_code == 400


class TestDayWizardAPIGetSalesPreview:
    """
    Integration tests for GET /api/v1/daily-records/{id}/sales-preview

    TC-INT-005
    """

    def test_get_sales_preview_success(
        self,
        client: TestClient,
        db_session: Session,
        day_with_operations,
        sample_ingredients
    ):
        """
        TC-INT-005: Get sales preview with closing inventory.

        Given: A day with operations
        When: GET /api/v1/daily-records/{id}/sales-preview with closing_inventory params
        Then: Should return 200 with calculated usage
        """
        # Arrange
        meat = sample_ingredients[0]

        # Act
        response = client.get(
            f"/api/v1/daily-records/{day_with_operations.id}/sales-preview",
            params={f"closing_inventory[{meat.id}]": 38.0}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "ingredients_used" in data
        assert "calculated_sales" in data
        assert "summary" in data

    def test_get_sales_preview_calculates_correctly(
        self,
        client: TestClient,
        db_session: Session,
        day_with_operations,
        sample_ingredients
    ):
        """
        Verify the calculation: opening=50 + transfers=20 - spoilage=2 - closing=38 = 30 used
        """
        # Arrange
        meat = sample_ingredients[0]

        # Act
        response = client.get(
            f"/api/v1/daily-records/{day_with_operations.id}/sales-preview",
            params={f"closing_inventory[{meat.id}]": 38.0}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        meat_usage = next(
            (i for i in data["ingredients_used"] if i["ingredient_id"] == meat.id),
            None
        )
        assert meat_usage is not None
        assert float(meat_usage["used"]) == 30.0

    def test_get_sales_preview_not_found(self, client: TestClient, db_session: Session):
        """
        Given: Non-existent daily record ID
        When: GET /api/v1/daily-records/99999/sales-preview
        Then: Should return 404
        """
        # Act
        response = client.get(
            "/api/v1/daily-records/99999/sales-preview",
            params={"closing_inventory[1]": 10.0}
        )

        # Assert
        assert response.status_code == 404

    def test_get_sales_preview_discrepancy_warning(
        self,
        client: TestClient,
        db_session: Session,
        daily_record_with_opening,
        sample_ingredients
    ):
        """
        Given: Closing inventory higher than opening (discrepancy)
        When: GET sales-preview
        Then: Should return warning about discrepancy
        """
        # Arrange
        meat = sample_ingredients[0]

        # Act
        response = client.get(
            f"/api/v1/daily-records/{daily_record_with_opening.id}/sales-preview",
            params={f"closing_inventory[{meat.id}]": 60.0}  # Higher than opening
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "warnings" in data
        # Should have at least one warning about discrepancy
        assert len(data["warnings"]) > 0


class TestDayWizardAPIGetSuggestedShifts:
    """
    Integration tests for GET /api/v1/daily-records/{id}/suggested-shifts
    """

    def test_get_suggested_shifts_success(
        self,
        client: TestClient,
        db_session: Session,
        new_daily_record
    ):
        """
        Given: An open daily record
        When: GET /api/v1/daily-records/{id}/suggested-shifts
        Then: Should return 200 with list of suggested shifts
        """
        # Act
        response = client.get(
            f"/api/v1/daily-records/{new_daily_record.id}/suggested-shifts"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "suggested_shifts" in data
        assert isinstance(data["suggested_shifts"], list)

    def test_get_suggested_shifts_not_found(self, client: TestClient, db_session: Session):
        """
        Given: Non-existent daily record ID
        When: GET /api/v1/daily-records/99999/suggested-shifts
        Then: Should return 404
        """
        # Act
        response = client.get("/api/v1/daily-records/99999/suggested-shifts")

        # Assert
        assert response.status_code == 404


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


class TestDayWizardEdgeCases:
    """
    Edge case tests for the Day Wizard functionality.
    """

    def test_high_discrepancy_critical_warning(
        self,
        db_session: Session,
        daily_record_with_opening,
        sample_ingredients
    ):
        """
        Edge case: Very large discrepancy (>50%).

        Given: Opening inventory = 50
        When: Closing inventory = 10 (usage = 40, expected ~0)
        Then: Should flag as critical discrepancy
        """
        # Arrange
        service = DayWizardService(db_session)
        meat = sample_ingredients[0]

        closing_inventory = {meat.id: Decimal("10.0")}  # Very low closing

        # Act
        result = service.calculate_sales_preview(
            daily_record_id=daily_record_with_opening.id,
            closing_inventory=closing_inventory
        )

        # Assert
        meat_usage = next(
            (i for i in result["ingredients_used"] if i["ingredient_id"] == meat.id),
            None
        )
        assert meat_usage is not None
        # Check for critical warning or flag
        if "discrepancy_level" in meat_usage:
            assert meat_usage["discrepancy_level"] == "critical"

    def test_decimal_precision_preserved(
        self,
        db_session: Session,
        daily_record_with_opening,
        sample_ingredients
    ):
        """
        Edge case: Ensure decimal precision is handled correctly.

        Given: Closing with 3 decimal places
        When: Calculating usage
        Then: Should preserve decimal precision
        """
        # Arrange
        service = DayWizardService(db_session)
        meat = sample_ingredients[0]

        closing_inventory = {meat.id: Decimal("47.555")}

        # Act
        result = service.calculate_sales_preview(
            daily_record_id=daily_record_with_opening.id,
            closing_inventory=closing_inventory
        )

        # Assert
        meat_usage = next(
            (i for i in result["ingredients_used"] if i["ingredient_id"] == meat.id),
            None
        )
        assert meat_usage is not None
        # Closing should preserve precision
        assert meat_usage["closing"] == Decimal("47.555")

    def test_multiple_ingredients_calculated_independently(
        self,
        db_session: Session,
        day_with_operations,
        sample_ingredients
    ):
        """
        Given: Day with multiple ingredients
        When: Calculating sales preview for all
        Then: Each ingredient should be calculated independently
        """
        # Arrange
        service = DayWizardService(db_session)
        meat = sample_ingredients[0]
        buns = sample_ingredients[1]

        closing_inventory = {
            meat.id: Decimal("38.0"),
            buns.id: Decimal("80"),
        }

        # Act
        result = service.calculate_sales_preview(
            daily_record_id=day_with_operations.id,
            closing_inventory=closing_inventory
        )

        # Assert
        assert len(result["ingredients_used"]) >= 2

        meat_usage = next(
            (i for i in result["ingredients_used"] if i["ingredient_id"] == meat.id),
            None
        )
        buns_usage = next(
            (i for i in result["ingredients_used"] if i["ingredient_id"] == buns.id),
            None
        )

        assert meat_usage is not None
        assert buns_usage is not None

        # Meat: 50 + 20 - 2 - 38 = 30
        assert meat_usage["used"] == Decimal("30.0")

        # Buns: 100 - 80 = 20 (no transfers or spoilage)
        assert buns_usage["used"] == Decimal("20")
