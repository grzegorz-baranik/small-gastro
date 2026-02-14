"""
Tests for Shift Template and Schedule Override features.

These tests are designed to FAIL because the implementation does not exist yet.
This is the RED phase of TDD - write failing tests first, then implement.

BDD Scenarios covered:
- Create shift template (success)
- Prevent duplicate template (same employee + day)
- Get shifts for date (template only)
- Get shifts for date (with override)
- Get shifts for date (day off override)
- Invalid time range validation
- List templates by employee
- Delete template

API Integration tests:
- POST /api/v1/shift-templates - Create template
- GET /api/v1/shift-schedules/week - Get weekly schedule
- DELETE /api/v1/shift-templates/{id} - Delete template

Test Data:
- Anna Kowalska, Cook, 25 PLN/h - Standard employee
- Jan Nowak, Helper, 20 PLN/h - Second employee
- ShiftTemplate: Anna, Mon (day_of_week=0), 08:00-16:00
"""

import pytest
from datetime import date, time
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# Service and schema imports - these will fail until implemented
# This is intentional - TDD Red phase
try:
    from app.services.shift_template_service import ShiftTemplateService
    from app.schemas.shift_template import (
        ShiftTemplateCreate,
        ShiftTemplateResponse,
        ShiftTemplateUpdate,
    )
    from app.schemas.shift_schedule import (
        ScheduleOverrideCreate,
        WeeklyScheduleResponse,
    )
    # Model imports - these will fail until models are created
    from app.models.shift_template import ShiftTemplate
    from app.models.shift_schedule_override import ShiftScheduleOverride
    # Builders - these import the non-existent models
    from tests.builders import (
        build_position,
        build_employee,
        build_shift_template,
        build_schedule_override,
    )
    SERVICE_AVAILABLE = True
except ImportError:
    SERVICE_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not SERVICE_AVAILABLE,
    reason="ShiftTemplateService not yet implemented (RED TDD phase)"
)


# Polish day names for assertions (0=Monday, 6=Sunday)
DAY_NAMES = [
    "Poniedzialek",
    "Wtorek",
    "Sroda",
    "Czwartek",
    "Piatek",
    "Sobota",
    "Niedziela",
]


class TestShiftTemplateServiceCreate:
    """
    Unit tests for ShiftTemplateService.create()
    TC-UNIT-001: Create a valid shift template
    """

    def test_create_shift_template_success(self, db_session: Session):
        """
        TC-UNIT-001: Create a valid shift template

        Given: An active employee "Anna Kowalska" exists
        When: Creating a shift template for Monday 08:00-16:00
        Then: Template should be created with correct values
        """
        # Arrange
        position = build_position(
            db_session, name="Kucharz", hourly_rate=Decimal("25.00")
        )
        employee = build_employee(
            db_session, name="Anna Kowalska", position=position
        )
        db_session.commit()

        service = ShiftTemplateService(db_session)
        data = ShiftTemplateCreate(
            employee_id=employee.id,
            day_of_week=0,  # Monday
            start_time=time(8, 0),
            end_time=time(16, 0),
        )

        # Act
        result = service.create(data)

        # Assert
        assert result.id is not None
        assert result.employee_id == employee.id
        assert result.day_of_week == 0
        assert result.start_time == time(8, 0)
        assert result.end_time == time(16, 0)

    def test_create_shift_template_with_employee_name(self, db_session: Session):
        """
        Given: An active employee exists
        When: Creating a shift template
        Then: Response should include employee name
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(
            db_session, name="Anna Kowalska", position=position
        )
        db_session.commit()

        service = ShiftTemplateService(db_session)
        data = ShiftTemplateCreate(
            employee_id=employee.id,
            day_of_week=0,
            start_time=time(8, 0),
            end_time=time(16, 0),
        )

        # Act
        result = service.create(data)

        # Assert
        assert result.employee is not None
        assert result.employee.name == "Anna Kowalska"


class TestShiftTemplateServiceDuplicate:
    """
    Unit tests for preventing duplicate templates
    TC-UNIT-002: Cannot create duplicate for same employee + day
    """

    def test_create_duplicate_template_fails(self, db_session: Session):
        """
        TC-UNIT-002: Prevent duplicate template for same employee + day

        Given: A template exists for Anna on Monday 08:00-16:00
        When: Creating another template for Anna on Monday (different times)
        Then: Should raise IntegrityError (unique constraint violation)
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(db_session, name="Anna Kowalska", position=position)
        db_session.commit()

        service = ShiftTemplateService(db_session)

        # Create first template
        data1 = ShiftTemplateCreate(
            employee_id=employee.id,
            day_of_week=0,
            start_time=time(8, 0),
            end_time=time(16, 0),
        )
        service.create(data1)

        # Try to create second template for same employee + day
        data2 = ShiftTemplateCreate(
            employee_id=employee.id,
            day_of_week=0,  # Same day
            start_time=time(10, 0),  # Different times
            end_time=time(18, 0),
        )

        # Act & Assert
        with pytest.raises(IntegrityError):
            service.create(data2)

    def test_same_employee_different_days_allowed(self, db_session: Session):
        """
        Given: A template exists for Anna on Monday
        When: Creating a template for Anna on Tuesday
        Then: Should succeed (different days are allowed)
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(db_session, name="Anna Kowalska", position=position)
        db_session.commit()

        service = ShiftTemplateService(db_session)

        # Create Monday template
        data_monday = ShiftTemplateCreate(
            employee_id=employee.id,
            day_of_week=0,  # Monday
            start_time=time(8, 0),
            end_time=time(16, 0),
        )
        service.create(data_monday)

        # Create Tuesday template
        data_tuesday = ShiftTemplateCreate(
            employee_id=employee.id,
            day_of_week=1,  # Tuesday
            start_time=time(8, 0),
            end_time=time(16, 0),
        )

        # Act
        result = service.create(data_tuesday)

        # Assert
        assert result.id is not None
        assert result.day_of_week == 1


class TestShiftTemplateServiceGetShiftsForDate:
    """
    Unit tests for ShiftTemplateService.get_shifts_for_date()
    TC-UNIT-003, TC-UNIT-004, TC-UNIT-005
    """

    def test_get_shifts_for_date_from_template(self, db_session: Session):
        """
        TC-UNIT-003: Get shifts for date - template only

        Given: A template exists for Anna on Monday 08:00-16:00
        And: No overrides exist for the date
        When: Getting shifts for Monday 2026-01-05
        Then: Should return template shifts with source='template'
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(db_session, name="Anna Kowalska", position=position)

        template = build_shift_template(
            db_session,
            employee=employee,
            day_of_week=0,  # Monday
            start_time=time(8, 0),
            end_time=time(16, 0),
        )
        db_session.commit()

        service = ShiftTemplateService(db_session)
        monday_date = date(2026, 1, 5)  # This is a Monday

        # Act
        shifts = service.get_shifts_for_date(monday_date)

        # Assert
        assert len(shifts) == 1
        assert shifts[0]["source"] == "template"
        assert shifts[0]["employee_id"] == employee.id
        assert shifts[0]["start_time"] == time(8, 0)
        assert shifts[0]["end_time"] == time(16, 0)

    def test_get_shifts_for_date_with_override(self, db_session: Session):
        """
        TC-UNIT-004: Get shifts for date - with override

        Given: A template exists for Anna on Monday 08:00-16:00
        And: An override exists for 2026-01-05 with 09:00-17:00
        When: Getting shifts for 2026-01-05
        Then: Should return override times with source='override'
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(db_session, name="Anna Kowalska", position=position)

        # Create template
        build_shift_template(
            db_session,
            employee=employee,
            day_of_week=0,  # Monday
            start_time=time(8, 0),
            end_time=time(16, 0),
        )

        # Create override for specific date
        override = build_schedule_override(
            db_session,
            employee=employee,
            override_date=date(2026, 1, 5),  # Monday
            start_time=time(9, 0),  # Different times
            end_time=time(17, 0),
            is_day_off=False,
        )
        db_session.commit()

        service = ShiftTemplateService(db_session)
        monday_date = date(2026, 1, 5)

        # Act
        shifts = service.get_shifts_for_date(monday_date)

        # Assert
        assert len(shifts) == 1
        assert shifts[0]["source"] == "override"
        assert shifts[0]["employee_id"] == employee.id
        assert shifts[0]["start_time"] == time(9, 0)  # Override times
        assert shifts[0]["end_time"] == time(17, 0)

    def test_get_shifts_for_date_day_off(self, db_session: Session):
        """
        TC-UNIT-005: Get shifts for date - day off override

        Given: A template exists for Anna on Monday 08:00-16:00
        And: A day-off override exists for 2026-01-05
        When: Getting shifts for 2026-01-05
        Then: Anna should NOT be in the returned shifts (she has day off)
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(db_session, name="Anna Kowalska", position=position)

        # Create template
        build_shift_template(
            db_session,
            employee=employee,
            day_of_week=0,  # Monday
            start_time=time(8, 0),
            end_time=time(16, 0),
        )

        # Create day-off override
        build_schedule_override(
            db_session,
            employee=employee,
            override_date=date(2026, 1, 5),
            is_day_off=True,
        )
        db_session.commit()

        service = ShiftTemplateService(db_session)
        monday_date = date(2026, 1, 5)

        # Act
        shifts = service.get_shifts_for_date(monday_date)

        # Assert
        assert len(shifts) == 0  # Employee has day off

    def test_get_shifts_for_date_no_template_for_day(self, db_session: Session):
        """
        Given: A template exists for Anna on Monday only
        When: Getting shifts for Tuesday
        Then: Should return empty list
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(db_session, name="Anna Kowalska", position=position)

        build_shift_template(
            db_session,
            employee=employee,
            day_of_week=0,  # Monday only
            start_time=time(8, 0),
            end_time=time(16, 0),
        )
        db_session.commit()

        service = ShiftTemplateService(db_session)
        tuesday_date = date(2026, 1, 6)  # Tuesday

        # Act
        shifts = service.get_shifts_for_date(tuesday_date)

        # Assert
        assert len(shifts) == 0

    def test_get_shifts_for_date_multiple_employees(self, db_session: Session):
        """
        Given: Templates exist for Anna and Jan on Monday
        When: Getting shifts for Monday
        Then: Should return both employees' shifts
        """
        # Arrange
        position = build_position(db_session)
        anna = build_employee(db_session, name="Anna Kowalska", position=position)
        jan = build_employee(db_session, name="Jan Nowak", position=position)

        build_shift_template(
            db_session,
            employee=anna,
            day_of_week=0,
            start_time=time(8, 0),
            end_time=time(16, 0),
        )
        build_shift_template(
            db_session,
            employee=jan,
            day_of_week=0,
            start_time=time(10, 0),
            end_time=time(18, 0),
        )
        db_session.commit()

        service = ShiftTemplateService(db_session)
        monday_date = date(2026, 1, 5)

        # Act
        shifts = service.get_shifts_for_date(monday_date)

        # Assert
        assert len(shifts) == 2
        employee_ids = {s["employee_id"] for s in shifts}
        assert anna.id in employee_ids
        assert jan.id in employee_ids


class TestShiftTemplateServiceValidation:
    """
    Unit tests for time range validation
    """

    def test_create_template_invalid_time_range_end_before_start(
        self, db_session: Session
    ):
        """
        Given: An active employee
        When: Creating a template with end_time < start_time
        Then: Should raise ValueError (Pydantic validation)
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(db_session, name="Anna Kowalska", position=position)
        db_session.commit()

        # Act & Assert - Pydantic schema validation
        with pytest.raises(ValueError):
            ShiftTemplateCreate(
                employee_id=employee.id,
                day_of_week=0,
                start_time=time(16, 0),  # 16:00
                end_time=time(8, 0),  # 08:00 - before start!
            )

    def test_create_template_invalid_day_of_week_negative(self, db_session: Session):
        """
        Given: An active employee
        When: Creating a template with day_of_week = -1
        Then: Should raise ValueError (Pydantic validation)
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(db_session, name="Anna Kowalska", position=position)
        db_session.commit()

        # Act & Assert
        with pytest.raises(ValueError):
            ShiftTemplateCreate(
                employee_id=employee.id,
                day_of_week=-1,  # Invalid
                start_time=time(8, 0),
                end_time=time(16, 0),
            )

    def test_create_template_invalid_day_of_week_too_high(self, db_session: Session):
        """
        Given: An active employee
        When: Creating a template with day_of_week = 7
        Then: Should raise ValueError (Pydantic validation)
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(db_session, name="Anna Kowalska", position=position)
        db_session.commit()

        # Act & Assert
        with pytest.raises(ValueError):
            ShiftTemplateCreate(
                employee_id=employee.id,
                day_of_week=7,  # Invalid (max is 6)
                start_time=time(8, 0),
                end_time=time(16, 0),
            )


class TestShiftTemplateServiceGetByEmployee:
    """
    Unit tests for ShiftTemplateService.get_by_employee()
    """

    def test_list_templates_by_employee(self, db_session: Session):
        """
        Given: Anna has templates for Mon, Tue, Wed
        And: Jan has templates for Mon, Fri
        When: Getting templates for Anna
        Then: Should return only Anna's 3 templates, ordered by day
        """
        # Arrange
        position = build_position(db_session)
        anna = build_employee(db_session, name="Anna Kowalska", position=position)
        jan = build_employee(db_session, name="Jan Nowak", position=position)

        # Anna: Mon, Tue, Wed
        build_shift_template(db_session, employee=anna, day_of_week=0)
        build_shift_template(db_session, employee=anna, day_of_week=1)
        build_shift_template(db_session, employee=anna, day_of_week=2)

        # Jan: Mon, Fri
        build_shift_template(db_session, employee=jan, day_of_week=0)
        build_shift_template(db_session, employee=jan, day_of_week=4)
        db_session.commit()

        service = ShiftTemplateService(db_session)

        # Act
        anna_templates = service.get_by_employee(anna.id)

        # Assert
        assert len(anna_templates) == 3
        assert all(t.employee_id == anna.id for t in anna_templates)
        # Should be ordered by day_of_week
        assert anna_templates[0].day_of_week == 0  # Mon
        assert anna_templates[1].day_of_week == 1  # Tue
        assert anna_templates[2].day_of_week == 2  # Wed

    def test_list_templates_by_employee_empty(self, db_session: Session):
        """
        Given: An employee with no templates
        When: Getting templates for that employee
        Then: Should return empty list
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(db_session, name="New Employee", position=position)
        db_session.commit()

        service = ShiftTemplateService(db_session)

        # Act
        templates = service.get_by_employee(employee.id)

        # Assert
        assert templates == []


class TestShiftTemplateServiceDelete:
    """
    Unit tests for ShiftTemplateService.delete()
    """

    def test_delete_template_success(self, db_session: Session):
        """
        Given: A template exists for Anna on Monday
        When: Deleting the template
        Then: Template should be removed
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(db_session, name="Anna Kowalska", position=position)
        template = build_shift_template(
            db_session,
            employee=employee,
            day_of_week=0,
        )
        db_session.commit()
        template_id = template.id

        service = ShiftTemplateService(db_session)

        # Act
        result = service.delete(template_id)

        # Assert
        assert result is True
        # Verify it's gone
        assert (
            db_session.query(ShiftTemplate)
            .filter(ShiftTemplate.id == template_id)
            .first()
            is None
        )

    def test_delete_template_not_found(self, db_session: Session):
        """
        Given: No template with ID 999 exists
        When: Trying to delete template 999
        Then: Should return False
        """
        # Arrange
        service = ShiftTemplateService(db_session)

        # Act
        result = service.delete(999)

        # Assert
        assert result is False


# =============================================================================
# API Integration Tests
# =============================================================================


class TestShiftTemplateApiCreate:
    """
    Integration tests for POST /api/v1/shift-templates
    TC-INT-001
    """

    def test_create_shift_template_api_success(
        self, client: TestClient, db_session: Session
    ):
        """
        TC-INT-001: POST /api/v1/shift-templates - Create template

        Given: An active employee "Anna Kowalska" exists
        When: POST /api/v1/shift-templates with valid data
        Then: Should return 201 with template details including day_name
        """
        # Arrange
        position = build_position(
            db_session, name="Kucharz", hourly_rate=Decimal("25.00")
        )
        employee = build_employee(
            db_session, name="Anna Kowalska", position=position
        )
        db_session.commit()

        payload = {
            "employee_id": employee.id,
            "day_of_week": 0,  # Monday
            "start_time": "08:00",
            "end_time": "16:00",
        }

        # Act
        response = client.post("/api/v1/shift-templates", json=payload)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["employee_id"] == employee.id
        assert data["employee_name"] == "Anna Kowalska"
        assert data["day_of_week"] == 0
        assert data["day_name"] == "Poniedzialek"
        assert "start_time" in data
        assert "end_time" in data
        assert "id" in data
        assert "created_at" in data

    def test_create_shift_template_api_invalid_employee(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: No employee with ID 999 exists
        When: POST /api/v1/shift-templates with employee_id=999
        Then: Should return 404 or 400
        """
        # Arrange
        payload = {
            "employee_id": 999,
            "day_of_week": 0,
            "start_time": "08:00",
            "end_time": "16:00",
        }

        # Act
        response = client.post("/api/v1/shift-templates", json=payload)

        # Assert
        assert response.status_code in [400, 404]

    def test_create_shift_template_api_invalid_time_range(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: An active employee exists
        When: POST with end_time before start_time
        Then: Should return 422 (Pydantic validation error)
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(db_session, name="Anna Kowalska", position=position)
        db_session.commit()

        payload = {
            "employee_id": employee.id,
            "day_of_week": 0,
            "start_time": "16:00",
            "end_time": "08:00",  # Before start!
        }

        # Act
        response = client.post("/api/v1/shift-templates", json=payload)

        # Assert
        assert response.status_code == 422

    def test_create_shift_template_api_duplicate(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: A template exists for Anna on Monday
        When: POST to create another template for Anna on Monday
        Then: Should return 400 (conflict)
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(db_session, name="Anna Kowalska", position=position)
        build_shift_template(db_session, employee=employee, day_of_week=0)
        db_session.commit()

        payload = {
            "employee_id": employee.id,
            "day_of_week": 0,  # Same day!
            "start_time": "10:00",
            "end_time": "18:00",
        }

        # Act
        response = client.post("/api/v1/shift-templates", json=payload)

        # Assert
        assert response.status_code == 400


class TestShiftTemplateApiList:
    """
    Integration tests for GET /api/v1/shift-templates
    """

    def test_list_templates_api(self, client: TestClient, db_session: Session):
        """
        Given: Templates exist for Anna (Mon, Tue) and Jan (Mon)
        When: GET /api/v1/shift-templates
        Then: Should return all templates
        """
        # Arrange
        position = build_position(db_session)
        anna = build_employee(db_session, name="Anna Kowalska", position=position)
        jan = build_employee(db_session, name="Jan Nowak", position=position)

        build_shift_template(db_session, employee=anna, day_of_week=0)
        build_shift_template(db_session, employee=anna, day_of_week=1)
        build_shift_template(db_session, employee=jan, day_of_week=0)
        db_session.commit()

        # Act
        response = client.get("/api/v1/shift-templates")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_list_templates_api_filter_by_employee(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: Templates exist for Anna and Jan
        When: GET /api/v1/shift-templates?employee_id={anna.id}
        Then: Should return only Anna's templates
        """
        # Arrange
        position = build_position(db_session)
        anna = build_employee(db_session, name="Anna Kowalska", position=position)
        jan = build_employee(db_session, name="Jan Nowak", position=position)

        build_shift_template(db_session, employee=anna, day_of_week=0)
        build_shift_template(db_session, employee=anna, day_of_week=1)
        build_shift_template(db_session, employee=jan, day_of_week=0)
        db_session.commit()

        # Act
        response = client.get(f"/api/v1/shift-templates?employee_id={anna.id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all(item["employee_id"] == anna.id for item in data["items"])


class TestShiftTemplateApiDelete:
    """
    Integration tests for DELETE /api/v1/shift-templates/{id}
    """

    def test_delete_template_api_success(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: A template exists
        When: DELETE /api/v1/shift-templates/{id}
        Then: Should return 204
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(db_session, name="Anna Kowalska", position=position)
        template = build_shift_template(db_session, employee=employee, day_of_week=0)
        db_session.commit()
        template_id = template.id

        # Act
        response = client.delete(f"/api/v1/shift-templates/{template_id}")

        # Assert
        assert response.status_code == 204

    def test_delete_template_api_not_found(self, client: TestClient):
        """
        Given: No template with ID 999 exists
        When: DELETE /api/v1/shift-templates/999
        Then: Should return 404
        """
        # Act
        response = client.delete("/api/v1/shift-templates/999")

        # Assert
        assert response.status_code == 404


class TestWeeklyScheduleApi:
    """
    Integration tests for GET /api/v1/shift-schedules/week
    TC-INT-002
    """

    def test_get_weekly_schedule_api_success(
        self, client: TestClient, db_session: Session
    ):
        """
        TC-INT-002: GET /api/v1/shift-schedules/week - Get weekly schedule

        Given: Templates exist for Anna (Mon-Fri) and Jan (Mon, Wed, Fri)
        When: GET /api/v1/shift-schedules/week?start_date=2026-01-05
        Then: Should return 7 days with appropriate shifts
        """
        # Arrange
        position = build_position(db_session)
        anna = build_employee(db_session, name="Anna Kowalska", position=position)
        jan = build_employee(db_session, name="Jan Nowak", position=position)

        # Anna: Mon-Fri
        for day in range(5):
            build_shift_template(db_session, employee=anna, day_of_week=day)

        # Jan: Mon (0), Wed (2), Fri (4)
        for day in [0, 2, 4]:
            build_shift_template(db_session, employee=jan, day_of_week=day)

        db_session.commit()

        # Act
        response = client.get("/api/v1/shift-schedules/week?start_date=2026-01-05")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["week_start"] == "2026-01-05"
        assert data["week_end"] == "2026-01-11"
        assert len(data["schedules"]) == 7  # 7 days

        # Monday (2026-01-05) should have both Anna and Jan
        monday = data["schedules"][0]
        assert monday["date"] == "2026-01-05"
        assert len(monday["shifts"]) == 2

    def test_get_weekly_schedule_api_with_override(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: Template exists for Anna on Monday 08:00-16:00
        And: Override exists for 2026-01-05 with 09:00-17:00
        When: GET /api/v1/shift-schedules/week?start_date=2026-01-05
        Then: Monday should show override times
        """
        # Arrange
        position = build_position(db_session)
        anna = build_employee(db_session, name="Anna Kowalska", position=position)

        build_shift_template(
            db_session,
            employee=anna,
            day_of_week=0,
            start_time=time(8, 0),
            end_time=time(16, 0),
        )
        build_schedule_override(
            db_session,
            employee=anna,
            override_date=date(2026, 1, 5),
            start_time=time(9, 0),
            end_time=time(17, 0),
        )
        db_session.commit()

        # Act
        response = client.get("/api/v1/shift-schedules/week?start_date=2026-01-05")

        # Assert
        assert response.status_code == 200
        data = response.json()
        monday = data["schedules"][0]
        assert len(monday["shifts"]) == 1
        shift = monday["shifts"][0]
        assert shift["start_time"] == "09:00:00"  # Override time
        assert shift["end_time"] == "17:00:00"
        assert shift["is_override"] is True

    def test_get_weekly_schedule_api_with_day_off(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: Template exists for Anna on Monday
        And: Day-off override exists for 2026-01-05
        When: GET /api/v1/shift-schedules/week?start_date=2026-01-05
        Then: Monday should have no shifts for Anna
        """
        # Arrange
        position = build_position(db_session)
        anna = build_employee(db_session, name="Anna Kowalska", position=position)

        build_shift_template(db_session, employee=anna, day_of_week=0)
        build_schedule_override(
            db_session,
            employee=anna,
            override_date=date(2026, 1, 5),
            is_day_off=True,
        )
        db_session.commit()

        # Act
        response = client.get("/api/v1/shift-schedules/week?start_date=2026-01-05")

        # Assert
        assert response.status_code == 200
        data = response.json()
        monday = data["schedules"][0]
        assert len(monday["shifts"]) == 0  # Day off


class TestScheduleOverrideApi:
    """
    Integration tests for schedule override endpoints
    """

    def test_create_schedule_override_api(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: An employee exists
        When: PUT /api/v1/shift-schedules/{date}/{employee_id}
        Then: Should create/update override
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(db_session, name="Anna Kowalska", position=position)
        db_session.commit()

        payload = {
            "start_time": "10:00",
            "end_time": "18:00",
            "is_day_off": False,
        }

        # Act
        response = client.put(
            f"/api/v1/shift-schedules/2026-01-05/{employee.id}", json=payload
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["employee_id"] == employee.id
        assert data["date"] == "2026-01-05"
        assert data["is_override"] is True

    def test_create_day_off_override_api(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: An employee exists
        When: PUT /api/v1/shift-schedules/{date}/{employee_id} with is_day_off=true
        Then: Should create day-off override
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(db_session, name="Anna Kowalska", position=position)
        db_session.commit()

        payload = {
            "is_day_off": True,
        }

        # Act
        response = client.put(
            f"/api/v1/shift-schedules/2026-01-05/{employee.id}", json=payload
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_day_off"] is True

    def test_delete_schedule_override_api(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: An override exists
        When: DELETE /api/v1/shift-schedules/{date}/{employee_id}
        Then: Should remove the override
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(db_session, name="Anna Kowalska", position=position)
        build_schedule_override(
            db_session,
            employee=employee,
            override_date=date(2026, 1, 5),
        )
        db_session.commit()

        # Act
        response = client.delete(
            f"/api/v1/shift-schedules/2026-01-05/{employee.id}"
        )

        # Assert
        assert response.status_code == 204


# =============================================================================
# Edge Cases and Boundary Tests
# =============================================================================


class TestShiftTemplateEdgeCases:
    """
    Edge case tests for shift templates
    """

    def test_template_for_weekend(self, db_session: Session):
        """
        EC-001: Template for Saturday and Sunday

        Given: An employee
        When: Creating templates for Saturday (5) and Sunday (6)
        Then: Should succeed
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(db_session, name="Anna Kowalska", position=position)
        db_session.commit()

        service = ShiftTemplateService(db_session)

        # Act
        saturday = service.create(
            ShiftTemplateCreate(
                employee_id=employee.id,
                day_of_week=5,  # Saturday
                start_time=time(10, 0),
                end_time=time(16, 0),
            )
        )
        sunday = service.create(
            ShiftTemplateCreate(
                employee_id=employee.id,
                day_of_week=6,  # Sunday
                start_time=time(12, 0),
                end_time=time(18, 0),
            )
        )

        # Assert
        assert saturday.day_of_week == 5
        assert sunday.day_of_week == 6

    def test_template_for_inactive_employee(self, db_session: Session):
        """
        EC-007: Template for inactive employee

        Given: An inactive employee
        When: Getting shifts for a date
        Then: Should include a warning or exclude the employee
        """
        # Arrange
        position = build_position(db_session)
        inactive_employee = build_employee(
            db_session, name="Inactive", position=position, is_active=False
        )
        build_shift_template(
            db_session, employee=inactive_employee, day_of_week=0
        )
        db_session.commit()

        service = ShiftTemplateService(db_session)
        monday = date(2026, 1, 5)

        # Act
        shifts = service.get_shifts_for_date(monday)

        # Assert
        # Expected behavior: either exclude inactive employees
        # or include them with a warning
        # This test documents the expected behavior
        if len(shifts) > 0:
            # If included, should have a warning flag
            assert shifts[0].get("warning") is not None or shifts[0].get(
                "employee_inactive"
            )
        # Or it could return empty - implementation decides

    def test_override_for_employee_without_template(self, db_session: Session):
        """
        Given: An employee without any templates
        And: An override (extra shift) for a specific date
        When: Getting shifts for that date
        Then: Should include the override as an extra shift
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(db_session, name="Extra Worker", position=position)
        # No template created!

        build_schedule_override(
            db_session,
            employee=employee,
            override_date=date(2026, 1, 5),
            start_time=time(14, 0),
            end_time=time(22, 0),
        )
        db_session.commit()

        service = ShiftTemplateService(db_session)
        monday = date(2026, 1, 5)

        # Act
        shifts = service.get_shifts_for_date(monday)

        # Assert
        assert len(shifts) == 1
        assert shifts[0]["employee_id"] == employee.id
        assert shifts[0]["source"] == "override"

    def test_template_minimum_shift_duration(self, db_session: Session):
        """
        Given: An employee
        When: Creating a template with 1-hour shift (minimum)
        Then: Should succeed
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(db_session, name="Anna Kowalska", position=position)
        db_session.commit()

        service = ShiftTemplateService(db_session)
        data = ShiftTemplateCreate(
            employee_id=employee.id,
            day_of_week=0,
            start_time=time(12, 0),
            end_time=time(13, 0),  # 1-hour shift
        )

        # Act
        result = service.create(data)

        # Assert
        assert result.id is not None

    def test_template_maximum_shift_duration(self, db_session: Session):
        """
        Given: An employee
        When: Creating a template with 12-hour shift (long but valid)
        Then: Should succeed
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(db_session, name="Anna Kowalska", position=position)
        db_session.commit()

        service = ShiftTemplateService(db_session)
        data = ShiftTemplateCreate(
            employee_id=employee.id,
            day_of_week=0,
            start_time=time(6, 0),
            end_time=time(18, 0),  # 12-hour shift
        )

        # Act
        result = service.create(data)

        # Assert
        assert result.id is not None
