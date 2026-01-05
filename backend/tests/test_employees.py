"""
Tests for Employee Management feature.

BDD Scenarios covered:
- Create employee with position's default rate
- Create employee with custom hourly rate
- Deactivate an employee
- Reactivate an inactive employee
- Filter employees by active status
- Cannot delete employee with wage history

Service tests (unit) and API tests (integration).
"""

import pytest
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services import employee_service
from app.services.employee_service import (
    EmployeeNotFoundError,
    PositionNotFoundError,
    EmployeeHasHistoryError,
)
from app.schemas.employee import EmployeeCreate, EmployeeUpdate

from tests.builders import (
    build_position,
    build_employee,
    build_shift_assignment,
    build_wage_transaction,
    build_daily_record,
)
from app.models.daily_record import DayStatus


class TestEmployeeEffectiveRate:
    """Tests for Employee.effective_hourly_rate property"""

    def test_effective_rate_with_override(self, db_session: Session):
        """
        Given: An employee with a custom hourly rate override
        When: Accessing effective_hourly_rate
        Then: Should return the override rate, not position's rate
        """
        # Arrange
        position = build_position(db_session, name="Kucharz", hourly_rate=Decimal("25.00"))
        employee = build_employee(
            db_session,
            name="Jan Kowalski",
            position=position,
            hourly_rate_override=Decimal("27.00")
        )
        db_session.commit()
        db_session.refresh(employee)

        # Act
        effective_rate = employee.effective_hourly_rate

        # Assert
        assert effective_rate == Decimal("27.00")

    def test_effective_rate_position_default(self, db_session: Session):
        """
        Given: An employee without hourly rate override
        When: Accessing effective_hourly_rate
        Then: Should return the position's default rate
        """
        # Arrange
        position = build_position(db_session, name="Kasjer", hourly_rate=Decimal("22.00"))
        employee = build_employee(
            db_session,
            name="Anna Nowak",
            position=position,
            hourly_rate_override=None
        )
        db_session.commit()
        db_session.refresh(employee)

        # Act
        effective_rate = employee.effective_hourly_rate

        # Assert
        assert effective_rate == Decimal("22.00")


class TestEmployeeServiceCreate:
    """Unit tests for EmployeeService.create()"""

    def test_create_employee_with_default_rate(self, db_session: Session):
        """
        Given: A position "Kasjer" exists with rate 22.00
        When: Creating an employee without custom rate
        Then: Employee should be created with position's default rate
        """
        # Arrange
        position = build_position(db_session, name="Kasjer", hourly_rate=Decimal("22.00"))
        db_session.commit()

        data = EmployeeCreate(
            name="Anna Nowak",
            position_id=position.id,
            hourly_rate=None,
            is_active=True
        )

        # Act
        result = employee_service.create_employee(db_session, data)

        # Assert
        assert result.id is not None
        assert result.name == "Anna Nowak"
        assert result.effective_hourly_rate == Decimal("22.00")

    def test_create_employee_with_custom_rate(self, db_session: Session):
        """
        Given: A position "Kasjer" exists with rate 22.00
        When: Creating an employee with custom rate 24.50
        Then: Employee should be created with the custom rate
        """
        # Arrange
        position = build_position(db_session, name="Kasjer", hourly_rate=Decimal("22.00"))
        db_session.commit()

        data = EmployeeCreate(
            name="Piotr Kowalski",
            position_id=position.id,
            hourly_rate=Decimal("24.50"),
            is_active=True
        )

        # Act
        result = employee_service.create_employee(db_session, data)

        # Assert
        assert result.id is not None
        assert result.name == "Piotr Kowalski"
        assert result.effective_hourly_rate == Decimal("24.50")

    def test_create_employee_position_not_found(self, db_session: Session):
        """
        Given: No position with ID 999 exists
        When: Creating an employee with position_id 999
        Then: Should raise PositionNotFoundError
        """
        # Arrange
        data = EmployeeCreate(
            name="Jan Kowalski",
            position_id=999,
            hourly_rate=None,
            is_active=True
        )

        # Act & Assert
        with pytest.raises(PositionNotFoundError):
            employee_service.create_employee(db_session, data)


class TestEmployeeServiceUpdate:
    """Unit tests for EmployeeService.update()"""

    def test_update_employee_name(self, db_session: Session):
        """
        Given: An employee exists
        When: Updating the name
        Then: Name should be updated
        """
        # Arrange
        employee = build_employee(db_session, name="Jan Kowalski")
        db_session.commit()

        data = EmployeeUpdate(name="Jan Nowak")

        # Act
        result = employee_service.update_employee(db_session, employee.id, data)

        # Assert
        assert result.name == "Jan Nowak"

    def test_update_employee_custom_rate(self, db_session: Session):
        """
        Given: An employee using position's default rate
        When: Setting a custom hourly rate
        Then: Employee should use the custom rate
        """
        # Arrange
        position = build_position(db_session, name="Kasjer", hourly_rate=Decimal("22.00"))
        employee = build_employee(
            db_session,
            name="Anna Nowak",
            position=position,
            hourly_rate_override=None
        )
        db_session.commit()

        data = EmployeeUpdate(hourly_rate=Decimal("25.00"))

        # Act
        result = employee_service.update_employee(db_session, employee.id, data)

        # Assert
        assert result.effective_hourly_rate == Decimal("25.00")

    def test_update_employee_change_position(self, db_session: Session):
        """
        Given: An employee in position "Kasjer"
        When: Changing position to "Kucharz"
        Then: Employee should be in the new position
        """
        # Arrange
        kasjer = build_position(db_session, name="Kasjer", hourly_rate=Decimal("22.00"))
        kucharz = build_position(db_session, name="Kucharz", hourly_rate=Decimal("25.00"))
        employee = build_employee(db_session, name="Anna Nowak", position=kasjer)
        db_session.commit()

        data = EmployeeUpdate(position_id=kucharz.id)

        # Act
        result = employee_service.update_employee(db_session, employee.id, data)

        # Assert
        assert result.position_id == kucharz.id
        assert result.position.name == "Kucharz"

    def test_update_employee_not_found(self, db_session: Session):
        """
        Given: No employee with ID 999 exists
        When: Updating employee 999
        Then: Should raise EmployeeNotFoundError
        """
        # Arrange
        data = EmployeeUpdate(name="New Name")

        # Act & Assert
        with pytest.raises(EmployeeNotFoundError):
            employee_service.update_employee(db_session, 999, data)

    def test_update_employee_invalid_position(self, db_session: Session):
        """
        Given: An employee exists
        When: Changing to non-existent position
        Then: Should raise PositionNotFoundError
        """
        # Arrange
        employee = build_employee(db_session, name="Jan Kowalski")
        db_session.commit()

        data = EmployeeUpdate(position_id=999)

        # Act & Assert
        with pytest.raises(PositionNotFoundError):
            employee_service.update_employee(db_session, employee.id, data)


class TestEmployeeServiceActivation:
    """Unit tests for employee activation/deactivation"""

    def test_deactivate_employee(self, db_session: Session):
        """
        Given: An active employee "Jan Kowalski"
        When: Deactivating the employee
        Then: Employee should be marked as inactive
        """
        # Arrange
        employee = build_employee(db_session, name="Jan Kowalski", is_active=True)
        db_session.commit()

        # Act
        result = employee_service.deactivate_employee(db_session, employee.id)

        # Assert
        assert result.is_active is False

    def test_activate_employee(self, db_session: Session):
        """
        Given: An inactive employee "Jan Kowalski"
        When: Activating the employee
        Then: Employee should be marked as active
        """
        # Arrange
        employee = build_employee(db_session, name="Jan Kowalski", is_active=False)
        db_session.commit()

        # Act
        result = employee_service.activate_employee(db_session, employee.id)

        # Assert
        assert result.is_active is True

    def test_deactivate_nonexistent_employee(self, db_session: Session):
        """
        Given: No employee with ID 999 exists
        When: Deactivating employee 999
        Then: Should raise EmployeeNotFoundError
        """
        # Act & Assert
        with pytest.raises(EmployeeNotFoundError):
            employee_service.deactivate_employee(db_session, 999)


class TestEmployeeServiceDelete:
    """Unit tests for EmployeeService.delete()"""

    def test_delete_employee_without_history(self, db_session: Session):
        """
        Given: An employee with no shift or wage history
        When: Deleting the employee
        Then: Employee should be successfully deleted
        """
        # Arrange
        employee = build_employee(db_session, name="Jan Kowalski")
        db_session.commit()
        employee_id = employee.id

        # Act
        result = employee_service.delete_employee(db_session, employee_id)

        # Assert
        assert result is True
        assert employee_service.get_employee(db_session, employee_id) is None

    def test_delete_employee_with_shifts_raises_error(self, db_session: Session):
        """
        Given: An employee with shift history
        When: Trying to delete the employee
        Then: Should raise EmployeeHasHistoryError
        """
        # Arrange
        daily_record = build_daily_record(db_session, status=DayStatus.OPEN)
        employee = build_employee(db_session, name="Jan Kowalski")
        build_shift_assignment(
            db_session,
            daily_record=daily_record,
            employee=employee
        )
        db_session.commit()

        # Act & Assert
        with pytest.raises(EmployeeHasHistoryError):
            employee_service.delete_employee(db_session, employee.id)

    def test_delete_employee_with_wages_raises_error(self, db_session: Session):
        """
        Given: An employee with wage transaction history
        When: Trying to delete the employee
        Then: Should raise EmployeeHasHistoryError with deactivation suggestion
        """
        # Arrange
        employee = build_employee(db_session, name="Jan Kowalski")
        db_session.commit()
        build_wage_transaction(db_session, employee_id=employee.id, amount=Decimal("4500.00"))
        db_session.commit()

        # Act & Assert
        with pytest.raises(EmployeeHasHistoryError):
            employee_service.delete_employee(db_session, employee.id)


class TestEmployeeServiceGet:
    """Unit tests for EmployeeService.get()"""

    def test_get_employees_active_only(self, db_session: Session):
        """
        Given: Active and inactive employees exist
        When: Getting employees without include_inactive
        Then: Only active employees should be returned
        """
        # Arrange
        position = build_position(db_session)
        build_employee(db_session, name="Jan Aktywny", position=position, is_active=True)
        build_employee(db_session, name="Anna Nieaktywna", position=position, is_active=False)
        db_session.commit()

        # Act
        employees = employee_service.get_employees(db_session, include_inactive=False)

        # Assert
        assert len(employees) == 1
        assert employees[0].name == "Jan Aktywny"

    def test_get_employees_include_inactive(self, db_session: Session):
        """
        Given: Active and inactive employees exist
        When: Getting employees with include_inactive=True
        Then: All employees should be returned
        """
        # Arrange
        position = build_position(db_session)
        build_employee(db_session, name="Jan Aktywny", position=position, is_active=True)
        build_employee(db_session, name="Anna Nieaktywna", position=position, is_active=False)
        db_session.commit()

        # Act
        employees = employee_service.get_employees(db_session, include_inactive=True)

        # Assert
        assert len(employees) == 2
        names = [e.name for e in employees]
        assert "Jan Aktywny" in names
        assert "Anna Nieaktywna" in names

    def test_get_employee_by_id(self, db_session: Session):
        """
        Given: An employee exists
        When: Getting employee by ID
        Then: Should return the employee with position loaded
        """
        # Arrange
        position = build_position(db_session, name="Kucharz")
        employee = build_employee(db_session, name="Jan Kowalski", position=position)
        db_session.commit()

        # Act
        result = employee_service.get_employee(db_session, employee.id)

        # Assert
        assert result is not None
        assert result.name == "Jan Kowalski"
        assert result.position.name == "Kucharz"


class TestEmployeeApiCreate:
    """Integration tests for POST /api/v1/employees"""

    def test_create_employee_api_with_default_rate(self, client: TestClient, db_session: Session):
        """
        Given: A position "Kasjer" with rate 22.00 exists
        When: POST /api/v1/employees without custom rate
        Then: Should return 201 with employee using position rate
        """
        # Arrange
        position = build_position(db_session, name="Kasjer", hourly_rate=Decimal("22.00"))
        db_session.commit()

        payload = {
            "name": "Anna Nowak",
            "position_id": position.id
        }

        # Act
        response = client.post("/api/v1/employees", json=payload)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Anna Nowak"
        assert data["position_name"] == "Kasjer"
        assert data["hourly_rate"] == "22.00"
        assert data["is_active"] is True

    def test_create_employee_api_with_custom_rate(self, client: TestClient, db_session: Session):
        """
        Given: A position "Kasjer" with rate 22.00 exists
        When: POST /api/v1/employees with custom rate 24.50
        Then: Should return 201 with employee using custom rate
        """
        # Arrange
        position = build_position(db_session, name="Kasjer", hourly_rate=Decimal("22.00"))
        db_session.commit()

        payload = {
            "name": "Piotr Kowalski",
            "position_id": position.id,
            "hourly_rate": "24.50"
        }

        # Act
        response = client.post("/api/v1/employees", json=payload)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Piotr Kowalski"
        assert data["hourly_rate"] == "24.50"

    def test_create_employee_api_invalid_position(self, client: TestClient):
        """
        Given: No position with ID 999 exists
        When: POST /api/v1/employees with position_id 999
        Then: Should return 400
        """
        # Arrange
        payload = {
            "name": "Jan Kowalski",
            "position_id": 999
        }

        # Act
        response = client.post("/api/v1/employees", json=payload)

        # Assert
        assert response.status_code == 400


class TestEmployeeApiGet:
    """Integration tests for GET /api/v1/employees"""

    def test_list_employees_api_active_only(self, client: TestClient, db_session: Session):
        """
        Given: Active and inactive employees exist
        When: GET /api/v1/employees (default)
        Then: Should return only active employees
        """
        # Arrange
        position = build_position(db_session)
        build_employee(db_session, name="Jan Aktywny", position=position, is_active=True)
        build_employee(db_session, name="Anna Nieaktywna", position=position, is_active=False)
        db_session.commit()

        # Act
        response = client.get("/api/v1/employees")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Jan Aktywny"

    def test_list_employees_api_include_inactive(self, client: TestClient, db_session: Session):
        """
        Given: Active and inactive employees exist
        When: GET /api/v1/employees?include_inactive=true
        Then: Should return all employees
        """
        # Arrange
        position = build_position(db_session)
        build_employee(db_session, name="Jan Aktywny", position=position, is_active=True)
        build_employee(db_session, name="Anna Nieaktywna", position=position, is_active=False)
        db_session.commit()

        # Act
        response = client.get("/api/v1/employees?include_inactive=true")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        names = [e["name"] for e in data["items"]]
        assert "Jan Aktywny" in names
        assert "Anna Nieaktywna" in names

    def test_get_active_employees_endpoint(self, client: TestClient, db_session: Session):
        """
        Given: Active and inactive employees exist
        When: GET /api/v1/employees/active
        Then: Should return only active employees
        """
        # Arrange
        position = build_position(db_session)
        build_employee(db_session, name="Jan Aktywny", position=position, is_active=True)
        build_employee(db_session, name="Anna Nieaktywna", position=position, is_active=False)
        db_session.commit()

        # Act
        response = client.get("/api/v1/employees/active")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Jan Aktywny"

    def test_get_employee_by_id_api(self, client: TestClient, db_session: Session):
        """
        Given: An employee exists
        When: GET /api/v1/employees/{id}
        Then: Should return the employee details
        """
        # Arrange
        position = build_position(db_session, name="Kucharz", hourly_rate=Decimal("25.00"))
        employee = build_employee(
            db_session,
            name="Jan Kowalski",
            position=position,
            hourly_rate_override=Decimal("27.00")
        )
        db_session.commit()

        # Act
        response = client.get(f"/api/v1/employees/{employee.id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Jan Kowalski"
        assert data["position_name"] == "Kucharz"
        assert data["hourly_rate"] == "27.00"

    def test_get_employee_not_found_api(self, client: TestClient):
        """
        Given: No employee with ID 999 exists
        When: GET /api/v1/employees/999
        Then: Should return 404
        """
        # Act
        response = client.get("/api/v1/employees/999")

        # Assert
        assert response.status_code == 404


class TestEmployeeApiUpdate:
    """Integration tests for PUT /api/v1/employees/{id}"""

    def test_update_employee_api_success(self, client: TestClient, db_session: Session):
        """
        Given: An employee exists
        When: PUT /api/v1/employees/{id} with new name
        Then: Should return updated employee
        """
        # Arrange
        employee = build_employee(db_session, name="Jan Kowalski")
        db_session.commit()

        payload = {"name": "Jan Nowak"}

        # Act
        response = client.put(f"/api/v1/employees/{employee.id}", json=payload)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Jan Nowak"

    def test_update_employee_api_not_found(self, client: TestClient):
        """
        Given: No employee with ID 999 exists
        When: PUT /api/v1/employees/999
        Then: Should return 404
        """
        # Arrange
        payload = {"name": "New Name"}

        # Act
        response = client.put("/api/v1/employees/999", json=payload)

        # Assert
        assert response.status_code == 404


class TestEmployeeApiActivation:
    """Integration tests for employee activation endpoints"""

    def test_deactivate_employee_api(self, client: TestClient, db_session: Session):
        """
        Given: An active employee exists
        When: PATCH /api/v1/employees/{id}/deactivate
        Then: Should return employee with is_active=False
        """
        # Arrange
        employee = build_employee(db_session, name="Jan Kowalski", is_active=True)
        db_session.commit()

        # Act
        response = client.patch(f"/api/v1/employees/{employee.id}/deactivate")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    def test_activate_employee_api(self, client: TestClient, db_session: Session):
        """
        Given: An inactive employee exists
        When: PATCH /api/v1/employees/{id}/activate
        Then: Should return employee with is_active=True
        """
        # Arrange
        employee = build_employee(db_session, name="Jan Kowalski", is_active=False)
        db_session.commit()

        # Act
        response = client.patch(f"/api/v1/employees/{employee.id}/activate")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True

    def test_deactivate_employee_api_not_found(self, client: TestClient):
        """
        Given: No employee with ID 999 exists
        When: PATCH /api/v1/employees/999/deactivate
        Then: Should return 404
        """
        # Act
        response = client.patch("/api/v1/employees/999/deactivate")

        # Assert
        assert response.status_code == 404


class TestEmployeeApiDelete:
    """Integration tests for DELETE /api/v1/employees/{id}"""

    def test_delete_employee_api_success(self, client: TestClient, db_session: Session):
        """
        Given: An employee with no history exists
        When: DELETE /api/v1/employees/{id}
        Then: Should return 204
        """
        # Arrange
        employee = build_employee(db_session, name="Jan Kowalski")
        db_session.commit()
        employee_id = employee.id

        # Act
        response = client.delete(f"/api/v1/employees/{employee_id}")

        # Assert
        assert response.status_code == 204

        # Verify deletion
        get_response = client.get(f"/api/v1/employees/{employee_id}")
        assert get_response.status_code == 404

    def test_delete_employee_api_with_history(self, client: TestClient, db_session: Session):
        """
        Given: An employee with wage history exists
        When: DELETE /api/v1/employees/{id}
        Then: Should return 400 with suggestion to deactivate
        """
        # Arrange
        employee = build_employee(db_session, name="Jan Kowalski")
        db_session.commit()
        build_wage_transaction(db_session, employee_id=employee.id)
        db_session.commit()

        # Act
        response = client.delete(f"/api/v1/employees/{employee.id}")

        # Assert
        assert response.status_code == 400

    def test_delete_employee_api_not_found(self, client: TestClient):
        """
        Given: No employee with ID 999 exists
        When: DELETE /api/v1/employees/999
        Then: Should return 404
        """
        # Act
        response = client.delete("/api/v1/employees/999")

        # Assert
        assert response.status_code == 404


class TestEmployeeEdgeCases:
    """Edge case tests for Employee feature"""

    def test_employee_keeps_custom_rate_after_position_change(self, db_session: Session):
        """
        Given: An employee with custom rate 27.00 in position "Kucharz" (25.00)
        When: Changing position to "Kasjer" (22.00)
        Then: Employee should keep the custom rate 27.00
        """
        # Arrange
        kucharz = build_position(db_session, name="Kucharz", hourly_rate=Decimal("25.00"))
        kasjer = build_position(db_session, name="Kasjer", hourly_rate=Decimal("22.00"))
        employee = build_employee(
            db_session,
            name="Jan Kowalski",
            position=kucharz,
            hourly_rate_override=Decimal("27.00")
        )
        db_session.commit()

        # Act
        data = EmployeeUpdate(position_id=kasjer.id)
        result = employee_service.update_employee(db_session, employee.id, data)

        # Assert
        assert result.position_id == kasjer.id
        assert result.effective_hourly_rate == Decimal("27.00")

    def test_employee_uses_new_position_rate_when_no_override(self, db_session: Session):
        """
        Given: An employee without custom rate in position "Kucharz" (25.00)
        When: Changing position to "Manager" (35.00)
        Then: Employee should use the new position rate
        """
        # Arrange
        kucharz = build_position(db_session, name="Kucharz", hourly_rate=Decimal("25.00"))
        manager = build_position(db_session, name="Manager", hourly_rate=Decimal("35.00"))
        employee = build_employee(
            db_session,
            name="Jan Kowalski",
            position=kucharz,
            hourly_rate_override=None
        )
        db_session.commit()

        # Act
        data = EmployeeUpdate(position_id=manager.id)
        result = employee_service.update_employee(db_session, employee.id, data)
        db_session.refresh(result)

        # Assert
        assert result.position_id == manager.id
        assert result.effective_hourly_rate == Decimal("35.00")
