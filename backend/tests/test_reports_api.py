"""
Tests for Bug Fix 3: Reports API endpoints changed from POST to GET.

Bug Description:
- All 6 report endpoints were using POST method
- This is incorrect RESTful design for read-only operations
- Fix changed all endpoints to GET with Query parameters

Test Scenarios:
- GET /reports/monthly-trends with start_date and end_date query params
- GET /reports/ingredient-usage with optional ingredient_ids
- GET /reports/spoilage with optional group_by parameter
- Verify POST requests return 405 Method Not Allowed
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.daily_record import DayStatus
from app.models.inventory_snapshot import SnapshotType
from app.models.spoilage import SpoilageReason

from tests.builders import (
    build_ingredient,
    build_daily_record,
    build_inventory_snapshot,
    build_spoilage,
    build_delivery,
)


class TestReportsApiGetMethods:
    """Tests for reports API using GET method (Bug 3 fix)."""

    # -------------------------------------------------------------------------
    # Monthly Trends Report Tests
    # -------------------------------------------------------------------------

    def test_get_monthly_trends_with_query_params(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: Date range as query parameters
        When: GET /api/v1/reports/monthly-trends?start_date=...&end_date=...
        Then: Monthly trends report should be returned
        """
        # Arrange
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        # Act
        response = client.get(
            "/api/v1/reports/monthly-trends",
            params={
                "start_date": str(start_date),
                "end_date": str(end_date),
            }
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify response structure (MonthlyTrendsReportResponse)
        assert "start_date" in data
        assert "end_date" in data
        assert "items" in data
        assert "days_count" in data

    def test_monthly_trends_post_returns_405(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: POST request to monthly-trends endpoint
        When: POST /api/v1/reports/monthly-trends
        Then: Should return 405 Method Not Allowed
        """
        # Arrange
        payload = {
            "start_date": str(date.today() - timedelta(days=30)),
            "end_date": str(date.today()),
        }

        # Act
        response = client.post("/api/v1/reports/monthly-trends", json=payload)

        # Assert
        assert response.status_code == 405  # Method Not Allowed

    def test_monthly_trends_requires_date_params(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: Missing required date parameters
        When: GET /api/v1/reports/monthly-trends (no params)
        Then: Should return 422 Unprocessable Entity
        """
        # Act
        response = client.get("/api/v1/reports/monthly-trends")

        # Assert
        assert response.status_code == 422  # Missing required params

    def test_monthly_trends_export_uses_get(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: Export endpoint with query parameters
        When: GET /api/v1/reports/monthly-trends/export
        Then: Should return Excel file (or 200)
        """
        # Arrange
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()

        # Act
        response = client.get(
            "/api/v1/reports/monthly-trends/export",
            params={
                "start_date": str(start_date),
                "end_date": str(end_date),
            }
        )

        # Assert
        assert response.status_code == 200
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers.get("content-type", "")

    # -------------------------------------------------------------------------
    # Ingredient Usage Report Tests
    # -------------------------------------------------------------------------

    def test_get_ingredient_usage_with_query_params(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: Date range as query parameters
        When: GET /api/v1/reports/ingredient-usage?start_date=...&end_date=...
        Then: Ingredient usage report should be returned
        """
        # Arrange
        start_date = date.today() - timedelta(days=14)
        end_date = date.today()

        # Act
        response = client.get(
            "/api/v1/reports/ingredient-usage",
            params={
                "start_date": str(start_date),
                "end_date": str(end_date),
            }
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify response structure (IngredientUsageReportResponse)
        assert "start_date" in data
        assert "end_date" in data
        assert "items" in data
        assert "summary" in data

    def test_ingredient_usage_with_optional_ingredient_ids(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: Date range and specific ingredient IDs
        When: GET /api/v1/reports/ingredient-usage?ingredient_ids=1,2,3
        Then: Report should filter by specified ingredients
        """
        # Arrange
        ingredient1 = build_ingredient(db_session, name="Mieso wolow", unit_label="kg")
        ingredient2 = build_ingredient(db_session, name="Cebula", unit_label="kg")
        db_session.commit()

        start_date = date.today() - timedelta(days=7)
        end_date = date.today()

        # Act
        response = client.get(
            "/api/v1/reports/ingredient-usage",
            params={
                "start_date": str(start_date),
                "end_date": str(end_date),
                "ingredient_ids": f"{ingredient1.id},{ingredient2.id}",
            }
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "summary" in data

    def test_ingredient_usage_post_returns_405(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: POST request to ingredient-usage endpoint
        When: POST /api/v1/reports/ingredient-usage
        Then: Should return 405 Method Not Allowed
        """
        # Arrange
        payload = {
            "start_date": str(date.today() - timedelta(days=7)),
            "end_date": str(date.today()),
        }

        # Act
        response = client.post("/api/v1/reports/ingredient-usage", json=payload)

        # Assert
        assert response.status_code == 405

    def test_ingredient_usage_export_uses_get(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: Export endpoint with query parameters
        When: GET /api/v1/reports/ingredient-usage/export
        Then: Should return Excel file
        """
        # Arrange
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()

        # Act
        response = client.get(
            "/api/v1/reports/ingredient-usage/export",
            params={
                "start_date": str(start_date),
                "end_date": str(end_date),
            }
        )

        # Assert
        assert response.status_code == 200
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers.get("content-type", "")

    # -------------------------------------------------------------------------
    # Spoilage Report Tests
    # -------------------------------------------------------------------------

    def test_get_spoilage_with_query_params(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: Date range as query parameters
        When: GET /api/v1/reports/spoilage?start_date=...&end_date=...
        Then: Spoilage report should be returned
        """
        # Arrange
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        # Act
        response = client.get(
            "/api/v1/reports/spoilage",
            params={
                "start_date": str(start_date),
                "end_date": str(end_date),
            }
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify response structure (SpoilageReportResponse)
        assert "start_date" in data
        assert "end_date" in data
        assert "items" in data
        assert "group_by" in data
        assert "total_count" in data

    def test_spoilage_with_group_by_parameter(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: group_by query parameter
        When: GET /api/v1/reports/spoilage?group_by=ingredient
        Then: Report should be grouped by ingredient
        """
        # Arrange
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()

        # Act - Test all valid group_by values
        for group_by in ["date", "ingredient", "reason"]:
            response = client.get(
                "/api/v1/reports/spoilage",
                params={
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "group_by": group_by,
                }
            )

            # Assert
            assert response.status_code == 200, f"Failed for group_by={group_by}"
            data = response.json()
            assert "group_by" in data
            assert data["group_by"] == group_by

    def test_spoilage_invalid_group_by_returns_400(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: Invalid group_by parameter
        When: GET /api/v1/reports/spoilage?group_by=invalid
        Then: Should return 400 Bad Request
        """
        # Arrange
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()

        # Act
        response = client.get(
            "/api/v1/reports/spoilage",
            params={
                "start_date": str(start_date),
                "end_date": str(end_date),
                "group_by": "invalid_value",
            }
        )

        # Assert
        assert response.status_code == 400

    def test_spoilage_post_returns_405(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: POST request to spoilage endpoint
        When: POST /api/v1/reports/spoilage
        Then: Should return 405 Method Not Allowed
        """
        # Arrange
        payload = {
            "start_date": str(date.today() - timedelta(days=7)),
            "end_date": str(date.today()),
        }

        # Act
        response = client.post("/api/v1/reports/spoilage", json=payload)

        # Assert
        assert response.status_code == 405

    def test_spoilage_export_uses_get(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: Export endpoint with query parameters
        When: GET /api/v1/reports/spoilage/export
        Then: Should return Excel file
        """
        # Arrange
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()

        # Act
        response = client.get(
            "/api/v1/reports/spoilage/export",
            params={
                "start_date": str(start_date),
                "end_date": str(end_date),
            }
        )

        # Assert
        assert response.status_code == 200
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers.get("content-type", "")

    # -------------------------------------------------------------------------
    # Daily Summary Report Tests (GET was already used, verify still works)
    # -------------------------------------------------------------------------

    def test_daily_summary_uses_get_with_path_param(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: A closed daily record
        When: GET /api/v1/reports/daily/{record_id}
        Then: Daily summary should be returned
        """
        # Arrange
        ingredient = build_ingredient(db_session, name="Test Skladnik")
        record = build_daily_record(
            db_session,
            record_date=date.today() - timedelta(days=1),
            status=DayStatus.CLOSED,
        )
        build_inventory_snapshot(
            db_session,
            daily_record_id=record.id,
            ingredient_id=ingredient.id,
            snapshot_type=SnapshotType.OPEN,
            quantity=Decimal("10.0"),
        )
        build_inventory_snapshot(
            db_session,
            daily_record_id=record.id,
            ingredient_id=ingredient.id,
            snapshot_type=SnapshotType.CLOSE,
            quantity=Decimal("5.0"),
        )
        db_session.commit()

        # Act
        response = client.get(f"/api/v1/reports/daily/{record.id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "date" in data
        assert "inventory_items" in data  # DailySummaryReportResponse field

    def test_daily_summary_export_uses_get(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: A daily record ID
        When: GET /api/v1/reports/daily/{record_id}/export
        Then: Should return Excel file
        """
        # Arrange
        ingredient = build_ingredient(db_session, name="Export Test")
        record = build_daily_record(
            db_session,
            record_date=date.today() - timedelta(days=2),
            status=DayStatus.CLOSED,
        )
        build_inventory_snapshot(
            db_session,
            daily_record_id=record.id,
            ingredient_id=ingredient.id,
            snapshot_type=SnapshotType.OPEN,
            quantity=Decimal("20.0"),
        )
        build_inventory_snapshot(
            db_session,
            daily_record_id=record.id,
            ingredient_id=ingredient.id,
            snapshot_type=SnapshotType.CLOSE,
            quantity=Decimal("10.0"),
        )
        db_session.commit()

        # Act
        response = client.get(f"/api/v1/reports/daily/{record.id}/export")

        # Assert
        assert response.status_code == 200
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers.get("content-type", "")


class TestReportsApiWithData:
    """Tests for reports API with actual data to verify correct results."""

    def test_spoilage_report_returns_data(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: Spoilage records exist in the database
        When: GET /api/v1/reports/spoilage
        Then: Report should contain the spoilage data
        """
        # Arrange
        ingredient = build_ingredient(db_session, name="Pomidory", unit_label="kg")
        record = build_daily_record(
            db_session,
            record_date=date.today(),
            status=DayStatus.OPEN,
        )
        build_inventory_snapshot(
            db_session,
            daily_record_id=record.id,
            ingredient_id=ingredient.id,
            snapshot_type=SnapshotType.OPEN,
            quantity=Decimal("10.0"),
        )
        spoilage = build_spoilage(
            db_session,
            daily_record_id=record.id,
            ingredient_id=ingredient.id,
            quantity=Decimal("2.5"),
            reason=SpoilageReason.EXPIRED,
            notes="Przeterminowane pomidory",
        )
        db_session.commit()

        start_date = date.today() - timedelta(days=1)
        end_date = date.today() + timedelta(days=1)

        # Act
        response = client.get(
            "/api/v1/reports/spoilage",
            params={
                "start_date": str(start_date),
                "end_date": str(end_date),
                "group_by": "date",
            }
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert len(data["items"]) >= 1
        # Find our spoilage record
        found = False
        for rec in data["items"]:
            if rec.get("ingredient_name") == "Pomidory":
                found = True
                assert rec["quantity"] == "2.5" or float(rec["quantity"]) == 2.5
                break
        assert found, "Spoilage record for 'Pomidory' not found in report"
