"""
Tests for Position Management feature.

BDD Scenarios covered:
- Create a new position with default rate
- Edit an existing position
- Cannot create position with duplicate name
- Cannot delete position with assigned employees
- Delete position without employees

Service tests (unit) and API tests (integration).
"""

import pytest
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services import position_service
from app.services.position_service import (
    PositionExistsError,
    PositionNotFoundError,
    PositionHasEmployeesError,
)
from app.schemas.position import PositionCreate, PositionUpdate

from tests.builders import build_position, build_employee


class TestPositionServiceCreate:
    """Unit tests for PositionService.create()"""

    def test_create_position_success(self, db_session: Session):
        """
        Given: No positions exist in the system
        When: Creating a new position with valid data
        Then: Position should be created with the given name and rate
        """
        # Arrange
        data = PositionCreate(name="Kucharz", hourly_rate=Decimal("25.00"))

        # Act
        result = position_service.create_position(db_session, data)

        # Assert
        assert result.id is not None
        assert result.name == "Kucharz"
        assert result.hourly_rate == Decimal("25.00")

    def test_create_position_duplicate_name_raises_error(self, db_session: Session):
        """
        Given: A position "Kucharz" already exists
        When: Trying to create another position with name "Kucharz"
        Then: Should raise PositionExistsError
        """
        # Arrange
        build_position(db_session, name="Kucharz", hourly_rate=Decimal("25.00"))
        db_session.commit()

        data = PositionCreate(name="Kucharz", hourly_rate=Decimal("30.00"))

        # Act & Assert
        with pytest.raises(PositionExistsError):
            position_service.create_position(db_session, data)

    def test_create_position_duplicate_name_case_insensitive(self, db_session: Session):
        """
        Given: A position "Kucharz" exists
        When: Trying to create a position with name "KUCHARZ" (different case)
        Then: Should raise PositionExistsError (case-insensitive check)
        """
        # Arrange
        build_position(db_session, name="Kucharz", hourly_rate=Decimal("25.00"))
        db_session.commit()

        data = PositionCreate(name="KUCHARZ", hourly_rate=Decimal("30.00"))

        # Act & Assert
        with pytest.raises(PositionExistsError):
            position_service.create_position(db_session, data)


class TestPositionServiceUpdate:
    """Unit tests for PositionService.update()"""

    def test_update_position_hourly_rate(self, db_session: Session):
        """
        Given: A position "Kucharz" exists with rate 25.00
        When: Updating the hourly rate to 27.00
        Then: The position rate should be updated
        """
        # Arrange
        position = build_position(db_session, name="Kucharz", hourly_rate=Decimal("25.00"))
        db_session.commit()

        data = PositionUpdate(hourly_rate=Decimal("27.00"))

        # Act
        result = position_service.update_position(db_session, position.id, data)

        # Assert
        assert result.hourly_rate == Decimal("27.00")
        assert result.name == "Kucharz"  # Name unchanged

    def test_update_position_name(self, db_session: Session):
        """
        Given: A position "Kucharz" exists
        When: Updating the name to "Szef Kuchni"
        Then: The position name should be updated
        """
        # Arrange
        position = build_position(db_session, name="Kucharz", hourly_rate=Decimal("25.00"))
        db_session.commit()

        data = PositionUpdate(name="Szef Kuchni")

        # Act
        result = position_service.update_position(db_session, position.id, data)

        # Assert
        assert result.name == "Szef Kuchni"
        assert result.hourly_rate == Decimal("25.00")  # Rate unchanged

    def test_update_position_not_found_raises_error(self, db_session: Session):
        """
        Given: No position with ID 999 exists
        When: Trying to update position 999
        Then: Should raise PositionNotFoundError
        """
        # Arrange
        data = PositionUpdate(hourly_rate=Decimal("30.00"))

        # Act & Assert
        with pytest.raises(PositionNotFoundError):
            position_service.update_position(db_session, 999, data)

    def test_update_position_name_conflict_raises_error(self, db_session: Session):
        """
        Given: Positions "Kucharz" and "Kasjer" exist
        When: Trying to rename "Kasjer" to "Kucharz"
        Then: Should raise PositionExistsError
        """
        # Arrange
        build_position(db_session, name="Kucharz", hourly_rate=Decimal("25.00"))
        kasjer = build_position(db_session, name="Kasjer", hourly_rate=Decimal("22.00"))
        db_session.commit()

        data = PositionUpdate(name="Kucharz")

        # Act & Assert
        with pytest.raises(PositionExistsError):
            position_service.update_position(db_session, kasjer.id, data)


class TestPositionServiceDelete:
    """Unit tests for PositionService.delete()"""

    def test_delete_position_without_employees(self, db_session: Session):
        """
        Given: A position "Pomocnik" exists with no employees assigned
        When: Deleting the position
        Then: Position should be successfully deleted
        """
        # Arrange
        position = build_position(db_session, name="Pomocnik", hourly_rate=Decimal("20.00"))
        db_session.commit()
        position_id = position.id

        # Act
        result = position_service.delete_position(db_session, position_id)

        # Assert
        assert result is True
        assert position_service.get_position(db_session, position_id) is None

    def test_delete_position_with_employees_raises_error(self, db_session: Session):
        """
        Given: A position "Kucharz" exists with an employee assigned
        When: Trying to delete the position
        Then: Should raise PositionHasEmployeesError
        """
        # Arrange
        position = build_position(db_session, name="Kucharz", hourly_rate=Decimal("25.00"))
        build_employee(db_session, name="Jan Kowalski", position=position)
        db_session.commit()

        # Act & Assert
        with pytest.raises(PositionHasEmployeesError):
            position_service.delete_position(db_session, position.id)

    def test_delete_position_not_found_raises_error(self, db_session: Session):
        """
        Given: No position with ID 999 exists
        When: Trying to delete position 999
        Then: Should raise PositionNotFoundError
        """
        # Act & Assert
        with pytest.raises(PositionNotFoundError):
            position_service.delete_position(db_session, 999)


class TestPositionServiceGet:
    """Unit tests for PositionService.get()"""

    def test_get_positions_returns_ordered_list(self, db_session: Session):
        """
        Given: Multiple positions exist
        When: Getting all positions
        Then: Positions should be returned ordered by name
        """
        # Arrange
        build_position(db_session, name="Kucharz", hourly_rate=Decimal("25.00"))
        build_position(db_session, name="Pomocnik", hourly_rate=Decimal("18.00"))
        build_position(db_session, name="Kasjer", hourly_rate=Decimal("22.00"))
        db_session.commit()

        # Act
        positions = position_service.get_positions(db_session)

        # Assert
        assert len(positions) == 3
        assert positions[0].name == "Kasjer"
        assert positions[1].name == "Kucharz"
        assert positions[2].name == "Pomocnik"

    def test_get_position_by_id(self, db_session: Session):
        """
        Given: A position exists
        When: Getting position by ID
        Then: Should return the position
        """
        # Arrange
        position = build_position(db_session, name="Kucharz", hourly_rate=Decimal("25.00"))
        db_session.commit()

        # Act
        result = position_service.get_position(db_session, position.id)

        # Assert
        assert result is not None
        assert result.name == "Kucharz"

    def test_get_position_not_found_returns_none(self, db_session: Session):
        """
        Given: No position with ID 999 exists
        When: Getting position 999
        Then: Should return None
        """
        # Act
        result = position_service.get_position(db_session, 999)

        # Assert
        assert result is None

    def test_get_employee_count_for_position(self, db_session: Session):
        """
        Given: A position with 2 employees assigned
        When: Getting employee count
        Then: Should return 2
        """
        # Arrange
        position = build_position(db_session, name="Kucharz", hourly_rate=Decimal("25.00"))
        build_employee(db_session, name="Jan Kowalski", position=position)
        build_employee(db_session, name="Anna Nowak", position=position)
        db_session.commit()

        # Act
        count = position_service.get_employee_count_for_position(db_session, position.id)

        # Assert
        assert count == 2


class TestPositionApiCreate:
    """Integration tests for POST /api/v1/positions"""

    def test_create_position_api_success(self, client: TestClient, db_session: Session):
        """
        Given: A valid position creation request
        When: POST /api/v1/positions
        Then: Should return 201 with the created position
        """
        # Arrange
        payload = {
            "name": "Kucharz",
            "hourly_rate": "25.00"
        }

        # Act
        response = client.post("/api/v1/positions", json=payload)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Kucharz"
        assert data["hourly_rate"] == "25.00"
        assert data["employee_count"] == 0
        assert "id" in data
        assert "created_at" in data

    def test_create_position_api_duplicate_name(self, client: TestClient, db_session: Session):
        """
        Given: A position "Kucharz" already exists
        When: POST /api/v1/positions with name "Kucharz"
        Then: Should return 400 with error message
        """
        # Arrange
        build_position(db_session, name="Kucharz", hourly_rate=Decimal("25.00"))
        db_session.commit()

        payload = {
            "name": "Kucharz",
            "hourly_rate": "30.00"
        }

        # Act
        response = client.post("/api/v1/positions", json=payload)

        # Assert
        assert response.status_code == 400
        assert "istnieje" in response.json()["detail"].lower()

    def test_create_position_api_validation_missing_name(self, client: TestClient):
        """
        Given: A position creation request without name
        When: POST /api/v1/positions
        Then: Should return 422 validation error
        """
        # Arrange
        payload = {
            "hourly_rate": "25.00"
        }

        # Act
        response = client.post("/api/v1/positions", json=payload)

        # Assert
        assert response.status_code == 422

    def test_create_position_api_validation_invalid_rate(self, client: TestClient):
        """
        Given: A position creation request with negative rate
        When: POST /api/v1/positions
        Then: Should return 422 validation error
        """
        # Arrange
        payload = {
            "name": "Kucharz",
            "hourly_rate": "-5.00"
        }

        # Act
        response = client.post("/api/v1/positions", json=payload)

        # Assert
        assert response.status_code == 422


class TestPositionApiGet:
    """Integration tests for GET /api/v1/positions"""

    def test_list_positions_api(self, client: TestClient, db_session: Session):
        """
        Given: Multiple positions exist
        When: GET /api/v1/positions
        Then: Should return list of positions with employee counts
        """
        # Arrange
        position1 = build_position(db_session, name="Kucharz", hourly_rate=Decimal("25.00"))
        build_position(db_session, name="Kasjer", hourly_rate=Decimal("22.00"))
        build_employee(db_session, name="Jan Kowalski", position=position1)
        db_session.commit()

        # Act
        response = client.get("/api/v1/positions")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        items = data["items"]
        assert len(items) == 2

        kucharz = next(p for p in items if p["name"] == "Kucharz")
        assert kucharz["employee_count"] == 1

        kasjer = next(p for p in items if p["name"] == "Kasjer")
        assert kasjer["employee_count"] == 0

    def test_get_position_by_id_api(self, client: TestClient, db_session: Session):
        """
        Given: A position exists
        When: GET /api/v1/positions/{id}
        Then: Should return the position with employee count
        """
        # Arrange
        position = build_position(db_session, name="Kucharz", hourly_rate=Decimal("25.00"))
        build_employee(db_session, name="Jan Kowalski", position=position)
        build_employee(db_session, name="Anna Nowak", position=position)
        db_session.commit()

        # Act
        response = client.get(f"/api/v1/positions/{position.id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Kucharz"
        assert data["hourly_rate"] == "25.00"
        assert data["employee_count"] == 2

    def test_get_position_not_found_api(self, client: TestClient):
        """
        Given: No position with ID 999 exists
        When: GET /api/v1/positions/999
        Then: Should return 404
        """
        # Act
        response = client.get("/api/v1/positions/999")

        # Assert
        assert response.status_code == 404


class TestPositionApiUpdate:
    """Integration tests for PUT /api/v1/positions/{id}"""

    def test_update_position_api_success(self, client: TestClient, db_session: Session):
        """
        Given: A position "Kucharz" with rate 25.00 exists
        When: PUT /api/v1/positions/{id} with new rate 27.00
        Then: Should return updated position
        """
        # Arrange
        position = build_position(db_session, name="Kucharz", hourly_rate=Decimal("25.00"))
        db_session.commit()

        payload = {
            "hourly_rate": "27.00"
        }

        # Act
        response = client.put(f"/api/v1/positions/{position.id}", json=payload)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["hourly_rate"] == "27.00"
        assert data["name"] == "Kucharz"

    def test_update_position_api_not_found(self, client: TestClient):
        """
        Given: No position with ID 999 exists
        When: PUT /api/v1/positions/999
        Then: Should return 404
        """
        # Arrange
        payload = {"hourly_rate": "30.00"}

        # Act
        response = client.put("/api/v1/positions/999", json=payload)

        # Assert
        assert response.status_code == 404

    def test_update_position_api_name_conflict(self, client: TestClient, db_session: Session):
        """
        Given: Positions "Kucharz" and "Kasjer" exist
        When: PUT /api/v1/positions/{kasjer_id} with name "Kucharz"
        Then: Should return 400
        """
        # Arrange
        build_position(db_session, name="Kucharz", hourly_rate=Decimal("25.00"))
        kasjer = build_position(db_session, name="Kasjer", hourly_rate=Decimal("22.00"))
        db_session.commit()

        payload = {"name": "Kucharz"}

        # Act
        response = client.put(f"/api/v1/positions/{kasjer.id}", json=payload)

        # Assert
        assert response.status_code == 400


class TestPositionApiDelete:
    """Integration tests for DELETE /api/v1/positions/{id}"""

    def test_delete_position_api_success(self, client: TestClient, db_session: Session):
        """
        Given: A position "Pomocnik" exists with no employees
        When: DELETE /api/v1/positions/{id}
        Then: Should return 204 and position should be gone
        """
        # Arrange
        position = build_position(db_session, name="Pomocnik", hourly_rate=Decimal("20.00"))
        db_session.commit()
        position_id = position.id

        # Act
        response = client.delete(f"/api/v1/positions/{position_id}")

        # Assert
        assert response.status_code == 204

        # Verify deletion
        get_response = client.get(f"/api/v1/positions/{position_id}")
        assert get_response.status_code == 404

    def test_delete_position_api_with_employees(self, client: TestClient, db_session: Session):
        """
        Given: A position "Kucharz" exists with an employee assigned
        When: DELETE /api/v1/positions/{id}
        Then: Should return 400 with error about assigned employees
        """
        # Arrange
        position = build_position(db_session, name="Kucharz", hourly_rate=Decimal("25.00"))
        build_employee(db_session, name="Jan Kowalski", position=position)
        db_session.commit()

        # Act
        response = client.delete(f"/api/v1/positions/{position.id}")

        # Assert
        assert response.status_code == 400
        assert "pracownik" in response.json()["detail"].lower()

    def test_delete_position_api_not_found(self, client: TestClient):
        """
        Given: No position with ID 999 exists
        When: DELETE /api/v1/positions/999
        Then: Should return 404
        """
        # Act
        response = client.delete("/api/v1/positions/999")

        # Assert
        assert response.status_code == 404


class TestPositionParameterized:
    """Parameterized tests for creating positions with different rates"""

    @pytest.mark.parametrize("name,rate", [
        ("Kucharz", "25.00"),
        ("Kasjer", "22.00"),
        ("Pomocnik", "18.50"),
        ("Manager", "35.00"),
    ])
    def test_create_various_positions(self, client: TestClient, db_session: Session, name: str, rate: str):
        """
        Test creating positions with different names and rates (from BDD Scenario Outline).
        """
        # Arrange
        payload = {"name": name, "hourly_rate": rate}

        # Act
        response = client.post("/api/v1/positions", json=payload)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == name
        assert data["hourly_rate"] == rate
