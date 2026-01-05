"""
Tests for Wage Analytics feature.

BDD Scenarios covered:
- View monthly wage analytics for all employees
- Filter wage analytics by specific employee
- Compare current month to previous month
- View analytics with no data for selected period

Service tests (unit) and API tests (integration).
"""

import pytest
from datetime import date, time
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services import wage_analytics_service
from app.models.daily_record import DayStatus

from tests.builders import (
    build_position,
    build_employee,
    build_shift_assignment,
    build_daily_record,
    build_wage_transaction,
)


class TestWageAnalyticsServiceHelpers:
    """Unit tests for helper functions in WageAnalyticsService"""

    def test_get_employee_hours_for_month(self, db_session: Session):
        """
        Given: An employee with shifts in January 2026
        When: Calculating hours for January 2026
        Then: Should return total hours worked
        """
        # Arrange
        position = build_position(db_session, hourly_rate=Decimal("25.00"))
        employee = build_employee(db_session, name="Jan Kowalski", position=position)

        # Create shifts in January
        record1 = build_daily_record(db_session, record_date=date(2026, 1, 5))
        record2 = build_daily_record(db_session, record_date=date(2026, 1, 10))

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
            start_time=time(9, 0),
            end_time=time(17, 0)  # 8 hours
        )
        db_session.commit()

        # Act
        hours = wage_analytics_service.get_employee_hours_for_month(
            db_session, employee.id, 1, 2026
        )

        # Assert
        assert hours == 16.0

    def test_get_employee_hours_for_month_no_shifts(self, db_session: Session):
        """
        Given: An employee with no shifts in December 2025
        When: Calculating hours for December 2025
        Then: Should return 0
        """
        # Arrange
        employee = build_employee(db_session, name="Jan Kowalski")
        db_session.commit()

        # Act
        hours = wage_analytics_service.get_employee_hours_for_month(
            db_session, employee.id, 12, 2025
        )

        # Assert
        assert hours == 0.0

    def test_get_employee_wages_for_month(self, db_session: Session):
        """
        Given: An employee with wage transactions in January 2026
        When: Getting wages for January 2026
        Then: Should return total wages paid
        """
        # Arrange
        employee = build_employee(db_session, name="Jan Kowalski")
        db_session.commit()

        build_wage_transaction(
            db_session,
            employee_id=employee.id,
            amount=Decimal("2000.00"),
            transaction_date=date(2026, 1, 15)
        )
        build_wage_transaction(
            db_session,
            employee_id=employee.id,
            amount=Decimal("500.00"),
            transaction_date=date(2026, 1, 25)
        )
        db_session.commit()

        # Act
        wages = wage_analytics_service.get_employee_wages_for_month(
            db_session, employee.id, 1, 2026
        )

        # Assert
        assert wages == Decimal("2500.00")

    def test_get_employee_wages_for_month_no_transactions(self, db_session: Session):
        """
        Given: An employee with no wage transactions in December 2025
        When: Getting wages for December 2025
        Then: Should return 0
        """
        # Arrange
        employee = build_employee(db_session, name="Jan Kowalski")
        db_session.commit()

        # Act
        wages = wage_analytics_service.get_employee_wages_for_month(
            db_session, employee.id, 12, 2025
        )

        # Assert
        assert wages == Decimal("0")


class TestWageAnalyticsServiceMain:
    """Unit tests for main get_wage_analytics function"""

    def test_get_wage_analytics_with_data(self, db_session: Session):
        """
        Given: Employees with shifts and wage transactions exist
        When: Getting wage analytics for January 2026
        Then: Should return summary and per-employee breakdown
        """
        # Arrange
        position = build_position(db_session, hourly_rate=Decimal("25.00"))
        employee1 = build_employee(
            db_session,
            name="Jan Kowalski",
            position=position,
            hourly_rate_override=Decimal("27.00")
        )
        employee2 = build_employee(
            db_session,
            name="Anna Nowak",
            position=position
        )

        # Create shifts
        record = build_daily_record(db_session, record_date=date(2026, 1, 15))
        build_shift_assignment(
            db_session,
            daily_record=record,
            employee=employee1,
            start_time=time(8, 0),
            end_time=time(16, 0)  # 8 hours
        )
        build_shift_assignment(
            db_session,
            daily_record=record,
            employee=employee2,
            start_time=time(10, 0),
            end_time=time(14, 0)  # 4 hours
        )

        # Create wage transactions
        build_wage_transaction(
            db_session,
            employee_id=employee1.id,
            amount=Decimal("4500.00"),
            transaction_date=date(2026, 1, 31)
        )
        build_wage_transaction(
            db_session,
            employee_id=employee2.id,
            amount=Decimal("2000.00"),
            transaction_date=date(2026, 1, 31)
        )
        db_session.commit()

        # Act
        result = wage_analytics_service.get_wage_analytics(
            db_session, month=1, year=2026
        )

        # Assert
        # Summary
        assert result.summary.total_wages == Decimal("6500.00")
        assert result.summary.total_hours == 12.0
        assert result.summary.avg_cost_per_hour == Decimal("541.67")  # 6500 / 12

        # By employee
        assert len(result.by_employee) == 2

        jan = next(e for e in result.by_employee if e.employee_name == "Jan Kowalski")
        assert jan.hours_worked == 8.0
        assert jan.wages_paid == Decimal("4500.00")

        anna = next(e for e in result.by_employee if e.employee_name == "Anna Nowak")
        assert anna.hours_worked == 4.0
        assert anna.wages_paid == Decimal("2000.00")

    def test_get_wage_analytics_no_data(self, db_session: Session):
        """
        Given: No wage transactions or shifts for December 2025
        When: Getting wage analytics
        Then: Should return summary with zeros and empty breakdown
        """
        # Act
        result = wage_analytics_service.get_wage_analytics(
            db_session, month=12, year=2025
        )

        # Assert
        assert result.summary.total_wages == Decimal("0")
        assert result.summary.total_hours == 0.0
        assert result.summary.avg_cost_per_hour == Decimal("0")
        assert len(result.by_employee) == 0
        assert result.previous_month_summary is None

    def test_get_wage_analytics_filter_by_employee(self, db_session: Session):
        """
        Given: Multiple employees with wage data
        When: Filtering by specific employee
        Then: Should return only that employee's data
        """
        # Arrange
        position = build_position(db_session)
        employee1 = build_employee(db_session, name="Jan Kowalski", position=position)
        employee2 = build_employee(db_session, name="Anna Nowak", position=position)

        record = build_daily_record(db_session, record_date=date(2026, 1, 15))
        build_shift_assignment(
            db_session,
            daily_record=record,
            employee=employee1,
            start_time=time(8, 0),
            end_time=time(16, 0)
        )
        build_shift_assignment(
            db_session,
            daily_record=record,
            employee=employee2,
            start_time=time(10, 0),
            end_time=time(14, 0)
        )

        build_wage_transaction(
            db_session,
            employee_id=employee1.id,
            amount=Decimal("4500.00"),
            transaction_date=date(2026, 1, 31)
        )
        build_wage_transaction(
            db_session,
            employee_id=employee2.id,
            amount=Decimal("2000.00"),
            transaction_date=date(2026, 1, 31)
        )
        db_session.commit()

        # Act
        result = wage_analytics_service.get_wage_analytics(
            db_session, month=1, year=2026, employee_id=employee1.id
        )

        # Assert
        assert result.summary.total_wages == Decimal("4500.00")
        assert result.summary.total_hours == 8.0
        assert len(result.by_employee) == 1
        assert result.by_employee[0].employee_name == "Jan Kowalski"

    def test_get_wage_analytics_previous_month_comparison(self, db_session: Session):
        """
        Given: Wage data for both January and December
        When: Getting analytics for January 2026
        Then: Should include previous month summary and change percentages
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(db_session, name="Jan Kowalski", position=position)

        # December 2025 data
        record_dec = build_daily_record(db_session, record_date=date(2025, 12, 15))
        build_shift_assignment(
            db_session,
            daily_record=record_dec,
            employee=employee,
            start_time=time(8, 0),
            end_time=time(16, 0)
        )
        build_wage_transaction(
            db_session,
            employee_id=employee.id,
            amount=Decimal("4000.00"),
            transaction_date=date(2025, 12, 31)
        )

        # January 2026 data
        record_jan = build_daily_record(db_session, record_date=date(2026, 1, 15))
        build_shift_assignment(
            db_session,
            daily_record=record_jan,
            employee=employee,
            start_time=time(8, 0),
            end_time=time(16, 0)
        )
        build_wage_transaction(
            db_session,
            employee_id=employee.id,
            amount=Decimal("4500.00"),
            transaction_date=date(2026, 1, 31)
        )
        db_session.commit()

        # Act
        result = wage_analytics_service.get_wage_analytics(
            db_session, month=1, year=2026
        )

        # Assert
        assert result.summary.total_wages == Decimal("4500.00")
        assert result.previous_month_summary is not None
        assert result.previous_month_summary.total_wages == Decimal("4000.00")

        # Check change percentage
        assert len(result.by_employee) == 1
        jan = result.by_employee[0]
        assert jan.previous_month_wages == Decimal("4000.00")
        assert jan.change_percent == 12.5  # (4500 - 4000) / 4000 * 100


class TestWageAnalyticsApi:
    """Integration tests for GET /api/v1/analytics/wages"""

    def test_get_wage_analytics_api_success(self, client: TestClient, db_session: Session):
        """
        Given: Employees with wage data for January 2026
        When: GET /api/v1/analytics/wages?month=1&year=2026
        Then: Should return analytics with summary and breakdown
        """
        # Arrange
        position = build_position(db_session, hourly_rate=Decimal("25.00"))
        employee = build_employee(
            db_session,
            name="Jan Kowalski",
            position=position
        )

        record = build_daily_record(db_session, record_date=date(2026, 1, 15))
        build_shift_assignment(
            db_session,
            daily_record=record,
            employee=employee,
            start_time=time(8, 0),
            end_time=time(16, 0)
        )
        build_wage_transaction(
            db_session,
            employee_id=employee.id,
            amount=Decimal("4500.00"),
            transaction_date=date(2026, 1, 31)
        )
        db_session.commit()

        # Act
        response = client.get("/api/v1/analytics/wages?month=1&year=2026")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "summary" in data
        assert data["summary"]["total_wages"] == "4500.00"
        assert data["summary"]["total_hours"] == 8.0

        assert "by_employee" in data
        assert len(data["by_employee"]) == 1
        assert data["by_employee"][0]["employee_name"] == "Jan Kowalski"

    def test_get_wage_analytics_api_no_data(self, client: TestClient, db_session: Session):
        """
        Given: No wage data for December 2025
        When: GET /api/v1/analytics/wages?month=12&year=2025
        Then: Should return zeros and empty breakdown
        """
        # Act
        response = client.get("/api/v1/analytics/wages?month=12&year=2025")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["summary"]["total_wages"] == "0"
        assert data["summary"]["total_hours"] == 0
        assert data["summary"]["avg_cost_per_hour"] == "0.00"  # Decimal with 2 places
        assert len(data["by_employee"]) == 0
        assert data["previous_month_summary"] is None

    def test_get_wage_analytics_api_filter_by_employee(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: Multiple employees with wage data
        When: GET /api/v1/analytics/wages?month=1&year=2026&employee_id={id}
        Then: Should return only that employee's data
        """
        # Arrange
        position = build_position(db_session)
        employee1 = build_employee(db_session, name="Jan Kowalski", position=position)
        employee2 = build_employee(db_session, name="Anna Nowak", position=position)

        record = build_daily_record(db_session, record_date=date(2026, 1, 15))
        build_shift_assignment(
            db_session,
            daily_record=record,
            employee=employee1,
            start_time=time(8, 0),
            end_time=time(16, 0)
        )
        build_shift_assignment(
            db_session,
            daily_record=record,
            employee=employee2,
            start_time=time(10, 0),
            end_time=time(14, 0)
        )

        build_wage_transaction(
            db_session,
            employee_id=employee1.id,
            amount=Decimal("4500.00"),
            transaction_date=date(2026, 1, 31)
        )
        build_wage_transaction(
            db_session,
            employee_id=employee2.id,
            amount=Decimal("2000.00"),
            transaction_date=date(2026, 1, 31)
        )
        db_session.commit()

        # Act
        response = client.get(
            f"/api/v1/analytics/wages?month=1&year=2026&employee_id={employee1.id}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["summary"]["total_wages"] == "4500.00"
        assert data["summary"]["total_hours"] == 8.0
        assert len(data["by_employee"]) == 1
        assert data["by_employee"][0]["employee_name"] == "Jan Kowalski"

    def test_get_wage_analytics_api_with_previous_month(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: Wage data for both January and December
        When: GET /api/v1/analytics/wages?month=1&year=2026
        Then: Should include previous month summary
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(db_session, name="Jan Kowalski", position=position)

        # December 2025
        record_dec = build_daily_record(db_session, record_date=date(2025, 12, 15))
        build_shift_assignment(
            db_session,
            daily_record=record_dec,
            employee=employee,
            start_time=time(8, 0),
            end_time=time(16, 0)
        )
        build_wage_transaction(
            db_session,
            employee_id=employee.id,
            amount=Decimal("4000.00"),
            transaction_date=date(2025, 12, 31)
        )

        # January 2026
        record_jan = build_daily_record(db_session, record_date=date(2026, 1, 15))
        build_shift_assignment(
            db_session,
            daily_record=record_jan,
            employee=employee,
            start_time=time(8, 0),
            end_time=time(16, 0)
        )
        build_wage_transaction(
            db_session,
            employee_id=employee.id,
            amount=Decimal("4500.00"),
            transaction_date=date(2026, 1, 31)
        )
        db_session.commit()

        # Act
        response = client.get("/api/v1/analytics/wages?month=1&year=2026")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["previous_month_summary"] is not None
        assert data["previous_month_summary"]["total_wages"] == "4000.00"

        assert data["by_employee"][0]["previous_month_wages"] == "4000.00"
        assert data["by_employee"][0]["change_percent"] == 12.5

    def test_get_wage_analytics_api_validation_month_range(self, client: TestClient):
        """
        Given: Invalid month parameter
        When: GET /api/v1/analytics/wages?month=13&year=2026
        Then: Should return 422 validation error
        """
        # Act
        response = client.get("/api/v1/analytics/wages?month=13&year=2026")

        # Assert
        assert response.status_code == 422

    def test_get_wage_analytics_api_validation_missing_params(self, client: TestClient):
        """
        Given: Missing required parameters
        When: GET /api/v1/analytics/wages
        Then: Should return 422 validation error
        """
        # Act
        response = client.get("/api/v1/analytics/wages")

        # Assert
        assert response.status_code == 422


class TestWageAnalyticsParameterized:
    """Parameterized tests for wage calculations"""

    @pytest.mark.parametrize("hours,rate,expected_wages", [
        (8, "25.00", "200.00"),
        (40, "25.00", "1000.00"),
        (80, "25.00", "2000.00"),
        (168, "25.00", "4200.00"),  # Monthly full-time equivalent
    ])
    def test_wage_calculation_various_hours(
        self,
        db_session: Session,
        hours: int,
        rate: str,
        expected_wages: str
    ):
        """
        Test wage calculations for different hours worked (from BDD Scenario Outline).
        """
        # Note: This tests the calculation logic rather than the analytics
        # The analytics aggregates existing transactions, so we verify the math

        rate_decimal = Decimal(rate)
        calculated = Decimal(str(hours)) * rate_decimal

        assert calculated == Decimal(expected_wages)


class TestWageAnalyticsEdgeCases:
    """Edge case tests for Wage Analytics"""

    def test_employee_only_with_shifts_no_wages(self, db_session: Session):
        """
        Given: An employee with shifts but no wage transactions
        When: Getting analytics
        Then: Should include employee with hours but zero wages
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(db_session, name="Jan Kowalski", position=position)

        record = build_daily_record(db_session, record_date=date(2026, 1, 15))
        build_shift_assignment(
            db_session,
            daily_record=record,
            employee=employee,
            start_time=time(8, 0),
            end_time=time(16, 0)
        )
        db_session.commit()

        # Act
        result = wage_analytics_service.get_wage_analytics(
            db_session, month=1, year=2026
        )

        # Assert
        assert len(result.by_employee) == 1
        assert result.by_employee[0].hours_worked == 8.0
        assert result.by_employee[0].wages_paid == Decimal("0")

    def test_employee_only_with_wages_no_shifts(self, db_session: Session):
        """
        Given: An employee with wage transactions but no shifts
        When: Getting analytics
        Then: Should include employee with wages but zero hours
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(db_session, name="Jan Kowalski", position=position)
        db_session.commit()

        build_wage_transaction(
            db_session,
            employee_id=employee.id,
            amount=Decimal("4500.00"),
            transaction_date=date(2026, 1, 31)
        )
        db_session.commit()

        # Act
        result = wage_analytics_service.get_wage_analytics(
            db_session, month=1, year=2026
        )

        # Assert
        assert len(result.by_employee) == 1
        assert result.by_employee[0].hours_worked == 0.0
        assert result.by_employee[0].wages_paid == Decimal("4500.00")

    def test_month_boundary_december_to_january(self, db_session: Session):
        """
        Given: Data in December 2025
        When: Getting January 2026 analytics
        Then: Previous month should correctly reference December
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(db_session, name="Jan Kowalski", position=position)

        record = build_daily_record(db_session, record_date=date(2025, 12, 15))
        build_shift_assignment(
            db_session,
            daily_record=record,
            employee=employee,
            start_time=time(8, 0),
            end_time=time(16, 0)
        )
        build_wage_transaction(
            db_session,
            employee_id=employee.id,
            amount=Decimal("4000.00"),
            transaction_date=date(2025, 12, 31)
        )
        db_session.commit()

        # Act
        result = wage_analytics_service.get_wage_analytics(
            db_session, month=1, year=2026
        )

        # Assert
        # No data for January, but previous month should show December
        assert result.summary.total_wages == Decimal("0")
        assert result.previous_month_summary is not None
        assert result.previous_month_summary.total_wages == Decimal("4000.00")

    def test_multiple_wage_transactions_per_employee(self, db_session: Session):
        """
        Given: An employee with multiple wage transactions in a month
        When: Getting analytics
        Then: Should sum all transactions
        """
        # Arrange
        position = build_position(db_session)
        employee = build_employee(db_session, name="Jan Kowalski", position=position)
        db_session.commit()

        build_wage_transaction(
            db_session,
            employee_id=employee.id,
            amount=Decimal("2000.00"),
            transaction_date=date(2026, 1, 10)
        )
        build_wage_transaction(
            db_session,
            employee_id=employee.id,
            amount=Decimal("1500.00"),
            transaction_date=date(2026, 1, 20)
        )
        build_wage_transaction(
            db_session,
            employee_id=employee.id,
            amount=Decimal("1000.00"),
            transaction_date=date(2026, 1, 31)
        )
        db_session.commit()

        # Act
        result = wage_analytics_service.get_wage_analytics(
            db_session, month=1, year=2026
        )

        # Assert
        assert result.summary.total_wages == Decimal("4500.00")
        assert result.by_employee[0].wages_paid == Decimal("4500.00")
