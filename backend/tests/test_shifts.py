"""
Tests for Shift Assignment feature.

BDD Scenarios covered:
- Add employee to current day's shift
- Add multiple employees to the same shift
- Cannot add shift with end time before start time
- Cannot close day without at least one employee
- Successfully close day with assigned employees
- Cannot modify shifts after day is closed
- Edit shift times while day is open
- Remove employee from shift while day is open

Service tests (unit) and API tests (integration).
"""

import pytest
from datetime import date, time
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services import shift_service
from app.services.shift_service import (
    ShiftNotFoundError,
    DailyRecordNotFoundError,
    DayNotOpenError,
    EmployeeNotFoundError,
    EmployeeAlreadyAssignedError,
    InvalidTimeRangeError,
)
from app.schemas.shift_assignment import ShiftAssignmentCreate, ShiftAssignmentUpdate
from app.models.daily_record import DayStatus

from tests.builders import (
    build_position,
    build_employee,
    build_shift_assignment,
    build_daily_record,
)


class TestShiftHoursWorkedCalculation:
    """Tests for ShiftAssignment.hours_worked property"""

    def test_hours_worked_full_shift(self, db_session: Session):
        """
        Given: A shift from 08:00 to 16:00
        When: Calculating hours worked
        Then: Should return 8.0 hours
        """
        # Arrange
        shift = build_shift_assignment(
            db_session,
            start_time=time(8, 0),
            end_time=time(16, 0)
        )
        db_session.commit()

        # Act
        hours = shift.hours_worked

        # Assert
        assert hours == 8.0

    def test_hours_worked_half_hour(self, db_session: Session):
        """
        Given: A shift from 08:00 to 16:30
        When: Calculating hours worked
        Then: Should return 8.5 hours
        """
        # Arrange
        shift = build_shift_assignment(
            db_session,
            start_time=time(8, 0),
            end_time=time(16, 30)
        )
        db_session.commit()

        # Act
        hours = shift.hours_worked

        # Assert
        assert hours == 8.5

    def test_hours_worked_short_shift(self, db_session: Session):
        """
        Given: A shift from 10:00 to 14:00
        When: Calculating hours worked
        Then: Should return 4.0 hours
        """
        # Arrange
        shift = build_shift_assignment(
            db_session,
            start_time=time(10, 0),
            end_time=time(14, 0)
        )
        db_session.commit()

        # Act
        hours = shift.hours_worked

        # Assert
        assert hours == 4.0


class TestShiftServiceCreate:
    """Unit tests for ShiftService.create_shift()"""

    def test_create_shift_success(self, db_session: Session):
        """
        Given: An open daily record and an active employee
        When: Creating a shift from 08:00 to 16:00
        Then: Shift should be created with hours calculated
        """
        # Arrange
        daily_record = build_daily_record(db_session, status=DayStatus.OPEN)
        position = build_position(db_session, hourly_rate=Decimal("25.00"))
        employee = build_employee(db_session, name="Jan Kowalski", position=position)
        db_session.commit()

        data = ShiftAssignmentCreate(
            employee_id=employee.id,
            start_time=time(8, 0),
            end_time=time(16, 0)
        )

        # Act
        result = shift_service.create_shift(db_session, daily_record.id, data)

        # Assert
        assert result.id is not None
        assert result.employee_id == employee.id
        assert result.hours_worked == 8.0

    def test_create_shift_end_before_start_raises_error(self, db_session: Session):
        """
        Given: An open daily record
        When: Creating a shift with end time before start time
        Then: Should raise ValidationError from Pydantic (schema validates first)

        Note: Pydantic validation happens before service layer is called.
        """
        # Arrange
        daily_record = build_daily_record(db_session, status=DayStatus.OPEN)
        employee = build_employee(db_session, name="Jan Kowalski")
        db_session.commit()

        # Act & Assert - Pydantic validates before service layer
        with pytest.raises(ValueError):
            ShiftAssignmentCreate(
                employee_id=employee.id,
                start_time=time(16, 0),
                end_time=time(8, 0)
            )

    def test_create_shift_closed_day_raises_error(self, db_session: Session):
        """
        Given: A closed daily record
        When: Trying to add a shift
        Then: Should raise DayNotOpenError
        """
        # Arrange
        daily_record = build_daily_record(db_session, status=DayStatus.CLOSED)
        employee = build_employee(db_session, name="Jan Kowalski")
        db_session.commit()

        data = ShiftAssignmentCreate(
            employee_id=employee.id,
            start_time=time(8, 0),
            end_time=time(16, 0)
        )

        # Act & Assert
        with pytest.raises(DayNotOpenError):
            shift_service.create_shift(db_session, daily_record.id, data)

    def test_create_shift_daily_record_not_found(self, db_session: Session):
        """
        Given: No daily record with ID 999 exists
        When: Trying to add a shift
        Then: Should raise DailyRecordNotFoundError
        """
        # Arrange
        employee = build_employee(db_session, name="Jan Kowalski")
        db_session.commit()

        data = ShiftAssignmentCreate(
            employee_id=employee.id,
            start_time=time(8, 0),
            end_time=time(16, 0)
        )

        # Act & Assert
        with pytest.raises(DailyRecordNotFoundError):
            shift_service.create_shift(db_session, 999, data)

    def test_create_shift_employee_not_found(self, db_session: Session):
        """
        Given: No employee with ID 999 exists
        When: Trying to add a shift for that employee
        Then: Should raise EmployeeNotFoundError
        """
        # Arrange
        daily_record = build_daily_record(db_session, status=DayStatus.OPEN)
        db_session.commit()

        data = ShiftAssignmentCreate(
            employee_id=999,
            start_time=time(8, 0),
            end_time=time(16, 0)
        )

        # Act & Assert
        with pytest.raises(EmployeeNotFoundError):
            shift_service.create_shift(db_session, daily_record.id, data)

    def test_create_shift_duplicate_employee_raises_error(self, db_session: Session):
        """
        Given: An employee already assigned to today's shift
        When: Trying to add the same employee again
        Then: Should raise EmployeeAlreadyAssignedError
        """
        # Arrange
        daily_record = build_daily_record(db_session, status=DayStatus.OPEN)
        employee = build_employee(db_session, name="Jan Kowalski")
        build_shift_assignment(
            db_session,
            daily_record=daily_record,
            employee=employee,
            start_time=time(8, 0),
            end_time=time(12, 0)
        )
        db_session.commit()

        data = ShiftAssignmentCreate(
            employee_id=employee.id,
            start_time=time(14, 0),
            end_time=time(18, 0)
        )

        # Act & Assert
        with pytest.raises(EmployeeAlreadyAssignedError):
            shift_service.create_shift(db_session, daily_record.id, data)


class TestShiftServiceUpdate:
    """Unit tests for ShiftService.update_shift()"""

    def test_update_shift_times(self, db_session: Session):
        """
        Given: A shift from 08:00 to 16:00 on an open day
        When: Updating end time to 17:00
        Then: Shift should be updated with new hours
        """
        # Arrange
        daily_record = build_daily_record(db_session, status=DayStatus.OPEN)
        employee = build_employee(db_session)
        shift = build_shift_assignment(
            db_session,
            daily_record=daily_record,
            employee=employee,
            start_time=time(8, 0),
            end_time=time(16, 0)
        )
        db_session.commit()

        data = ShiftAssignmentUpdate(
            start_time=time(8, 0),
            end_time=time(17, 0)
        )

        # Act
        result = shift_service.update_shift(db_session, daily_record.id, shift.id, data)

        # Assert
        assert result.hours_worked == 9.0

    def test_update_shift_on_closed_day_raises_error(self, db_session: Session):
        """
        Given: A shift on a closed day
        When: Trying to update the shift
        Then: Should raise DayNotOpenError
        """
        # Arrange
        daily_record = build_daily_record(db_session, status=DayStatus.OPEN)
        employee = build_employee(db_session)
        shift = build_shift_assignment(
            db_session,
            daily_record=daily_record,
            employee=employee
        )
        db_session.commit()

        # Close the day
        daily_record.status = DayStatus.CLOSED
        db_session.commit()

        data = ShiftAssignmentUpdate(
            start_time=time(9, 0),
            end_time=time(17, 0)
        )

        # Act & Assert
        with pytest.raises(DayNotOpenError):
            shift_service.update_shift(db_session, daily_record.id, shift.id, data)

    def test_update_shift_not_found(self, db_session: Session):
        """
        Given: An open daily record
        When: Updating a non-existent shift
        Then: Should raise ShiftNotFoundError
        """
        # Arrange
        daily_record = build_daily_record(db_session, status=DayStatus.OPEN)
        db_session.commit()

        data = ShiftAssignmentUpdate(
            start_time=time(9, 0),
            end_time=time(17, 0)
        )

        # Act & Assert
        with pytest.raises(ShiftNotFoundError):
            shift_service.update_shift(db_session, daily_record.id, 999, data)

    def test_update_shift_invalid_time_range(self, db_session: Session):
        """
        Given: A valid shift
        When: Updating with end time before start time
        Then: Should raise ValidationError from Pydantic (schema validates first)

        Note: Pydantic validation happens before service layer is called.
        """
        # Arrange
        daily_record = build_daily_record(db_session, status=DayStatus.OPEN)
        employee = build_employee(db_session)
        shift = build_shift_assignment(
            db_session,
            daily_record=daily_record,
            employee=employee
        )
        db_session.commit()

        # Act & Assert - Pydantic validates before service layer
        with pytest.raises(ValueError):
            ShiftAssignmentUpdate(
                start_time=time(16, 0),
                end_time=time(8, 0)
            )


class TestShiftServiceDelete:
    """Unit tests for ShiftService.delete_shift()"""

    def test_delete_shift_success(self, db_session: Session):
        """
        Given: A shift on an open day
        When: Deleting the shift
        Then: Shift should be successfully deleted
        """
        # Arrange
        daily_record = build_daily_record(db_session, status=DayStatus.OPEN)
        employee = build_employee(db_session)
        shift = build_shift_assignment(
            db_session,
            daily_record=daily_record,
            employee=employee
        )
        db_session.commit()
        shift_id = shift.id

        # Act
        result = shift_service.delete_shift(db_session, daily_record.id, shift_id)

        # Assert
        assert result is True
        assert shift_service.get_shift(db_session, shift_id) is None

    def test_delete_shift_on_closed_day_raises_error(self, db_session: Session):
        """
        Given: A shift on a closed day
        When: Trying to delete the shift
        Then: Should raise DayNotOpenError
        """
        # Arrange
        daily_record = build_daily_record(db_session, status=DayStatus.OPEN)
        employee = build_employee(db_session)
        shift = build_shift_assignment(
            db_session,
            daily_record=daily_record,
            employee=employee
        )
        db_session.commit()

        # Close the day
        daily_record.status = DayStatus.CLOSED
        db_session.commit()

        # Act & Assert
        with pytest.raises(DayNotOpenError):
            shift_service.delete_shift(db_session, daily_record.id, shift.id)


class TestShiftServiceHelpers:
    """Unit tests for ShiftService helper functions"""

    def test_count_shifts_for_day(self, db_session: Session):
        """
        Given: A day with 2 employees assigned
        When: Counting shifts
        Then: Should return 2
        """
        # Arrange
        daily_record = build_daily_record(db_session, status=DayStatus.OPEN)
        position = build_position(db_session)
        employee1 = build_employee(db_session, name="Jan Kowalski", position=position)
        employee2 = build_employee(db_session, name="Anna Nowak", position=position)
        build_shift_assignment(db_session, daily_record=daily_record, employee=employee1)
        build_shift_assignment(db_session, daily_record=daily_record, employee=employee2)
        db_session.commit()

        # Act
        count = shift_service.count_shifts_for_day(db_session, daily_record.id)

        # Assert
        assert count == 2

    def test_validate_minimum_employees_success(self, db_session: Session):
        """
        Given: A day with at least 1 employee
        When: Validating minimum employees
        Then: Should return True
        """
        # Arrange
        daily_record = build_daily_record(db_session, status=DayStatus.OPEN)
        employee = build_employee(db_session)
        build_shift_assignment(db_session, daily_record=daily_record, employee=employee)
        db_session.commit()

        # Act
        result = shift_service.validate_minimum_employees(db_session, daily_record.id)

        # Assert
        assert result is True

    def test_validate_minimum_employees_failure(self, db_session: Session):
        """
        Given: A day with no employees assigned
        When: Validating minimum employees
        Then: Should return False
        """
        # Arrange
        daily_record = build_daily_record(db_session, status=DayStatus.OPEN)
        db_session.commit()

        # Act
        result = shift_service.validate_minimum_employees(db_session, daily_record.id)

        # Assert
        assert result is False

    def test_calculate_hours_for_period(self, db_session: Session):
        """
        Given: An employee with multiple shifts in a week
        When: Calculating total hours for that week
        Then: Should return sum of all shift hours
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(db_session, position=position)

        # Create multiple daily records with shifts
        record1 = build_daily_record(db_session, record_date=date(2026, 1, 1))
        record2 = build_daily_record(db_session, record_date=date(2026, 1, 2))

        build_shift_assignment(
            db_session,
            daily_record=record1,
            employee=employee,
            start_time=time(8, 0),
            end_time=time(16, 0)  # 8 hours
        )
        build_shift_assignment(
            db_session,
            daily_record=record2,
            employee=employee,
            start_time=time(10, 0),
            end_time=time(18, 0)  # 8 hours
        )
        db_session.commit()

        # Act
        hours = shift_service.calculate_hours_for_period(
            db_session,
            employee.id,
            date(2026, 1, 1),
            date(2026, 1, 7)
        )

        # Assert
        assert hours == 16.0


class TestShiftApiCreate:
    """Integration tests for POST /api/v1/daily-records/{id}/shifts"""

    def test_create_shift_api_success(self, client: TestClient, db_session: Session):
        """
        Given: An open daily record and an active employee
        When: POST /api/v1/daily-records/{id}/shifts
        Then: Should return 201 with shift details including hours
        """
        # Arrange
        daily_record = build_daily_record(db_session, status=DayStatus.OPEN)
        position = build_position(db_session, hourly_rate=Decimal("25.00"))
        employee = build_employee(db_session, name="Jan Kowalski", position=position)
        db_session.commit()

        payload = {
            "employee_id": employee.id,
            "start_time": "08:00:00",
            "end_time": "16:00:00"
        }

        # Act
        response = client.post(
            f"/api/v1/daily-records/{daily_record.id}/shifts",
            json=payload
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["employee_id"] == employee.id
        assert data["employee_name"] == "Jan Kowalski"
        assert data["hours_worked"] == 8.0
        assert data["hourly_rate"] == "25.00"

    def test_create_shift_api_invalid_times(self, client: TestClient, db_session: Session):
        """
        Given: An open daily record
        When: POST with end time before start time
        Then: Should return 422 (Pydantic validation error)
        """
        # Arrange
        daily_record = build_daily_record(db_session, status=DayStatus.OPEN)
        employee = build_employee(db_session)
        db_session.commit()

        payload = {
            "employee_id": employee.id,
            "start_time": "16:00:00",
            "end_time": "08:00:00"
        }

        # Act
        response = client.post(
            f"/api/v1/daily-records/{daily_record.id}/shifts",
            json=payload
        )

        # Assert - Pydantic returns 422 for validation errors
        assert response.status_code == 422

    def test_create_shift_api_closed_day(self, client: TestClient, db_session: Session):
        """
        Given: A closed daily record
        When: POST to add shift
        Then: Should return 400
        """
        # Arrange
        daily_record = build_daily_record(db_session, status=DayStatus.CLOSED)
        employee = build_employee(db_session)
        db_session.commit()

        payload = {
            "employee_id": employee.id,
            "start_time": "08:00:00",
            "end_time": "16:00:00"
        }

        # Act
        response = client.post(
            f"/api/v1/daily-records/{daily_record.id}/shifts",
            json=payload
        )

        # Assert
        assert response.status_code == 400

    def test_create_shift_api_duplicate_employee(self, client: TestClient, db_session: Session):
        """
        Given: An employee already assigned to today's shift
        When: POST to add the same employee again
        Then: Should return 400
        """
        # Arrange
        daily_record = build_daily_record(db_session, status=DayStatus.OPEN)
        employee = build_employee(db_session)
        build_shift_assignment(db_session, daily_record=daily_record, employee=employee)
        db_session.commit()

        payload = {
            "employee_id": employee.id,
            "start_time": "14:00:00",
            "end_time": "18:00:00"
        }

        # Act
        response = client.post(
            f"/api/v1/daily-records/{daily_record.id}/shifts",
            json=payload
        )

        # Assert
        assert response.status_code == 400

    def test_create_shift_api_daily_record_not_found(self, client: TestClient, db_session: Session):
        """
        Given: No daily record with ID 999 exists
        When: POST to add shift
        Then: Should return 404
        """
        # Arrange
        employee = build_employee(db_session)
        db_session.commit()

        payload = {
            "employee_id": employee.id,
            "start_time": "08:00:00",
            "end_time": "16:00:00"
        }

        # Act
        response = client.post("/api/v1/daily-records/999/shifts", json=payload)

        # Assert
        assert response.status_code == 404


class TestShiftApiGet:
    """Integration tests for GET /api/v1/daily-records/{id}/shifts"""

    def test_list_shifts_api(self, client: TestClient, db_session: Session):
        """
        Given: A day with 2 employees assigned
        When: GET /api/v1/daily-records/{id}/shifts
        Then: Should return list of shifts with details
        """
        # Arrange
        daily_record = build_daily_record(db_session, status=DayStatus.OPEN)
        position = build_position(db_session, hourly_rate=Decimal("25.00"))
        employee1 = build_employee(
            db_session,
            name="Jan Kowalski",
            position=position
        )
        employee2 = build_employee(
            db_session,
            name="Anna Nowak",
            position=position
        )
        build_shift_assignment(
            db_session,
            daily_record=daily_record,
            employee=employee1,
            start_time=time(8, 0),
            end_time=time(16, 0)
        )
        build_shift_assignment(
            db_session,
            daily_record=daily_record,
            employee=employee2,
            start_time=time(10, 0),
            end_time=time(18, 0)
        )
        db_session.commit()

        # Act
        response = client.get(f"/api/v1/daily-records/{daily_record.id}/shifts")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

        # Verify order by start_time
        assert data["items"][0]["employee_name"] == "Jan Kowalski"
        assert data["items"][0]["hours_worked"] == 8.0
        assert data["items"][1]["employee_name"] == "Anna Nowak"
        assert data["items"][1]["hours_worked"] == 8.0


class TestShiftApiUpdate:
    """Integration tests for PUT /api/v1/daily-records/{id}/shifts/{shift_id}"""

    def test_update_shift_api_success(self, client: TestClient, db_session: Session):
        """
        Given: A shift from 08:00 to 16:00 on an open day
        When: PUT to update end time to 17:00
        Then: Should return updated shift with 9 hours
        """
        # Arrange
        daily_record = build_daily_record(db_session, status=DayStatus.OPEN)
        employee = build_employee(db_session)
        shift = build_shift_assignment(
            db_session,
            daily_record=daily_record,
            employee=employee,
            start_time=time(8, 0),
            end_time=time(16, 0)
        )
        db_session.commit()

        payload = {
            "start_time": "08:00:00",
            "end_time": "17:00:00"
        }

        # Act
        response = client.put(
            f"/api/v1/daily-records/{daily_record.id}/shifts/{shift.id}",
            json=payload
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["hours_worked"] == 9.0

    def test_update_shift_api_closed_day(self, client: TestClient, db_session: Session):
        """
        Given: A shift on a closed day
        When: PUT to update
        Then: Should return 400
        """
        # Arrange
        daily_record = build_daily_record(db_session, status=DayStatus.OPEN)
        employee = build_employee(db_session)
        shift = build_shift_assignment(
            db_session,
            daily_record=daily_record,
            employee=employee
        )
        db_session.commit()

        # Close the day
        daily_record.status = DayStatus.CLOSED
        db_session.commit()

        payload = {
            "start_time": "09:00:00",
            "end_time": "17:00:00"
        }

        # Act
        response = client.put(
            f"/api/v1/daily-records/{daily_record.id}/shifts/{shift.id}",
            json=payload
        )

        # Assert
        assert response.status_code == 400

    def test_update_shift_api_not_found(self, client: TestClient, db_session: Session):
        """
        Given: An open daily record
        When: PUT to update non-existent shift
        Then: Should return 404
        """
        # Arrange
        daily_record = build_daily_record(db_session, status=DayStatus.OPEN)
        db_session.commit()

        payload = {
            "start_time": "09:00:00",
            "end_time": "17:00:00"
        }

        # Act
        response = client.put(
            f"/api/v1/daily-records/{daily_record.id}/shifts/999",
            json=payload
        )

        # Assert
        assert response.status_code == 404


class TestShiftApiDelete:
    """Integration tests for DELETE /api/v1/daily-records/{id}/shifts/{shift_id}"""

    def test_delete_shift_api_success(self, client: TestClient, db_session: Session):
        """
        Given: A shift on an open day
        When: DELETE the shift
        Then: Should return 204
        """
        # Arrange
        daily_record = build_daily_record(db_session, status=DayStatus.OPEN)
        employee = build_employee(db_session)
        shift = build_shift_assignment(
            db_session,
            daily_record=daily_record,
            employee=employee
        )
        db_session.commit()

        # Act
        response = client.delete(
            f"/api/v1/daily-records/{daily_record.id}/shifts/{shift.id}"
        )

        # Assert
        assert response.status_code == 204

    def test_delete_shift_api_keeps_other_shifts(self, client: TestClient, db_session: Session):
        """
        Given: Two employees assigned to today's shift
        When: DELETE one employee's shift
        Then: Other employee should still be assigned
        """
        # Arrange
        daily_record = build_daily_record(db_session, status=DayStatus.OPEN)
        position = build_position(db_session)
        employee1 = build_employee(db_session, name="Jan Kowalski", position=position)
        employee2 = build_employee(db_session, name="Anna Nowak", position=position)
        shift1 = build_shift_assignment(
            db_session,
            daily_record=daily_record,
            employee=employee1
        )
        build_shift_assignment(
            db_session,
            daily_record=daily_record,
            employee=employee2
        )
        db_session.commit()

        # Act
        response = client.delete(
            f"/api/v1/daily-records/{daily_record.id}/shifts/{shift1.id}"
        )

        # Assert
        assert response.status_code == 204

        # Verify Anna is still assigned
        get_response = client.get(f"/api/v1/daily-records/{daily_record.id}/shifts")
        data = get_response.json()
        assert data["total"] == 1
        assert data["items"][0]["employee_name"] == "Anna Nowak"

    def test_delete_shift_api_closed_day(self, client: TestClient, db_session: Session):
        """
        Given: A shift on a closed day
        When: DELETE the shift
        Then: Should return 400
        """
        # Arrange
        daily_record = build_daily_record(db_session, status=DayStatus.OPEN)
        employee = build_employee(db_session)
        shift = build_shift_assignment(
            db_session,
            daily_record=daily_record,
            employee=employee
        )
        db_session.commit()

        # Close the day
        daily_record.status = DayStatus.CLOSED
        db_session.commit()

        # Act
        response = client.delete(
            f"/api/v1/daily-records/{daily_record.id}/shifts/{shift.id}"
        )

        # Assert
        assert response.status_code == 400


class TestShiftSchemaValidation:
    """Tests for shift schema validation (Pydantic)"""

    def test_schema_validates_end_time_after_start(self):
        """
        Given: A shift create request with end time before start time
        When: Creating ShiftAssignmentCreate
        Then: Should raise ValueError
        """
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ShiftAssignmentCreate(
                employee_id=1,
                start_time=time(16, 0),
                end_time=time(8, 0)
            )

        assert "zakonczenia" in str(exc_info.value).lower()

    def test_schema_validates_update_times(self):
        """
        Given: A shift update request with end time before start time
        When: Creating ShiftAssignmentUpdate
        Then: Should raise ValueError
        """
        # Act & Assert
        with pytest.raises(ValueError):
            ShiftAssignmentUpdate(
                start_time=time(16, 0),
                end_time=time(8, 0)
            )


class TestMultipleEmployeesShifts:
    """Integration tests for multiple employees on same day"""

    def test_add_multiple_employees_to_same_day(self, client: TestClient, db_session: Session):
        """
        Given: An open daily record
        When: Adding "Jan" (08:00-16:00) and "Anna" (10:00-18:00)
        Then: Both should be assigned with correct hours
        """
        # Arrange
        daily_record = build_daily_record(db_session, status=DayStatus.OPEN)
        position = build_position(db_session, hourly_rate=Decimal("25.00"))
        employee1 = build_employee(db_session, name="Jan Kowalski", position=position)
        employee2 = build_employee(db_session, name="Anna Nowak", position=position)
        db_session.commit()

        # Act
        response1 = client.post(
            f"/api/v1/daily-records/{daily_record.id}/shifts",
            json={
                "employee_id": employee1.id,
                "start_time": "08:00:00",
                "end_time": "16:00:00"
            }
        )
        response2 = client.post(
            f"/api/v1/daily-records/{daily_record.id}/shifts",
            json={
                "employee_id": employee2.id,
                "start_time": "10:00:00",
                "end_time": "18:00:00"
            }
        )

        # Assert
        assert response1.status_code == 201
        assert response2.status_code == 201

        # Get all shifts
        list_response = client.get(f"/api/v1/daily-records/{daily_record.id}/shifts")
        data = list_response.json()
        assert data["total"] == 2

        jan = next(s for s in data["items"] if s["employee_name"] == "Jan Kowalski")
        anna = next(s for s in data["items"] if s["employee_name"] == "Anna Nowak")

        assert jan["hours_worked"] == 8.0
        assert anna["hours_worked"] == 8.0
