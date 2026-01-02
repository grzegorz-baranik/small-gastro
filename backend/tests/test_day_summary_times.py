"""
Tests for Bug Fix 1: Day Summary times use ISO datetime format.

Bug Description:
- Frontend was getting RangeError when parsing times
- The service was returning "%H:%M" format which caused JS Date parsing to fail
- Fix changed `opening_time` and `closing_time` to use `.isoformat()` format

Test Scenarios:
- Day summary returns opening_time in ISO format
- Day summary returns closing_time in ISO format (for closed days)
- ISO format strings are parseable by standard datetime parsers
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
import re

from sqlalchemy.orm import Session

from app.services import daily_operations_service
from app.models.daily_record import DayStatus
from app.models.inventory_snapshot import SnapshotType, InventoryLocation

from tests.builders import (
    build_ingredient,
    build_daily_record,
    build_inventory_snapshot,
)


# ISO 8601 datetime pattern (with optional microseconds and timezone)
ISO_DATETIME_PATTERN = re.compile(
    r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?([+-]\d{2}:\d{2}|Z)?$'
)


class TestDaySummaryTimeFormat:
    """Tests for day summary time format (Bug 1 fix)."""

    def test_opening_time_is_iso_format_for_open_day(self, db_session: Session):
        """
        Given: An open daily record with opened_at timestamp
        When: Getting day summary
        Then: opening_time should be in ISO 8601 format
        """
        # Arrange
        ingredient = build_ingredient(db_session, name="Test Ingredient 1")
        daily_record = build_daily_record(
            db_session,
            record_date=date.today(),
            status=DayStatus.OPEN,
            opened_at=datetime(2024, 1, 15, 8, 30, 45),
        )
        build_inventory_snapshot(
            db_session,
            daily_record_id=daily_record.id,
            ingredient_id=ingredient.id,
            snapshot_type=SnapshotType.OPEN,
            quantity=Decimal("10.0"),
        )
        db_session.commit()

        # Act
        summary = daily_operations_service.get_day_summary(db_session, daily_record.id)

        # Assert
        assert summary is not None
        assert summary.opening_time is not None

        # Verify ISO format
        assert ISO_DATETIME_PATTERN.match(summary.opening_time), (
            f"opening_time '{summary.opening_time}' should be in ISO 8601 format"
        )

        # Verify the time can be parsed back
        parsed = datetime.fromisoformat(summary.opening_time)
        assert parsed.hour == 8
        assert parsed.minute == 30
        assert parsed.second == 45

    def test_closing_time_is_iso_format_for_closed_day(self, db_session: Session):
        """
        Given: A closed daily record with closed_at timestamp
        When: Getting day summary
        Then: closing_time should be in ISO 8601 format
        """
        # Arrange
        ingredient = build_ingredient(db_session, name="Test Ingredient 2")
        daily_record = build_daily_record(
            db_session,
            record_date=date.today() - timedelta(days=1),
            status=DayStatus.CLOSED,
            opened_at=datetime(2024, 1, 14, 9, 0, 0),
            closed_at=datetime(2024, 1, 14, 22, 15, 30),
        )
        # Add opening snapshot
        build_inventory_snapshot(
            db_session,
            daily_record_id=daily_record.id,
            ingredient_id=ingredient.id,
            snapshot_type=SnapshotType.OPEN,
            quantity=Decimal("10.0"),
        )
        # Add closing snapshot
        build_inventory_snapshot(
            db_session,
            daily_record_id=daily_record.id,
            ingredient_id=ingredient.id,
            snapshot_type=SnapshotType.CLOSE,
            quantity=Decimal("5.0"),
        )
        db_session.commit()

        # Act
        summary = daily_operations_service.get_day_summary(db_session, daily_record.id)

        # Assert
        assert summary is not None
        assert summary.closing_time is not None

        # Verify ISO format
        assert ISO_DATETIME_PATTERN.match(summary.closing_time), (
            f"closing_time '{summary.closing_time}' should be in ISO 8601 format"
        )

        # Verify the time can be parsed back
        parsed = datetime.fromisoformat(summary.closing_time)
        assert parsed.hour == 22
        assert parsed.minute == 15
        assert parsed.second == 30

    def test_closing_time_is_none_for_open_day(self, db_session: Session):
        """
        Given: An open daily record (not yet closed)
        When: Getting day summary
        Then: closing_time should be None
        """
        # Arrange
        ingredient = build_ingredient(db_session, name="Test Ingredient 3")
        daily_record = build_daily_record(
            db_session,
            record_date=date.today(),
            status=DayStatus.OPEN,
        )
        build_inventory_snapshot(
            db_session,
            daily_record_id=daily_record.id,
            ingredient_id=ingredient.id,
            snapshot_type=SnapshotType.OPEN,
            quantity=Decimal("10.0"),
        )
        db_session.commit()

        # Act
        summary = daily_operations_service.get_day_summary(db_session, daily_record.id)

        # Assert
        assert summary is not None
        assert summary.closing_time is None

    def test_both_times_are_iso_format_for_closed_day(self, db_session: Session):
        """
        Given: A closed daily record with both timestamps
        When: Getting day summary
        Then: Both opening_time and closing_time should be ISO format strings
        """
        # Arrange
        ingredient = build_ingredient(db_session, name="Test Ingredient 4")
        opened = datetime(2024, 1, 16, 10, 0, 0)
        closed = datetime(2024, 1, 16, 21, 30, 0)

        daily_record = build_daily_record(
            db_session,
            record_date=date(2024, 1, 16),
            status=DayStatus.CLOSED,
            opened_at=opened,
            closed_at=closed,
        )
        build_inventory_snapshot(
            db_session,
            daily_record_id=daily_record.id,
            ingredient_id=ingredient.id,
            snapshot_type=SnapshotType.OPEN,
            quantity=Decimal("20.0"),
        )
        build_inventory_snapshot(
            db_session,
            daily_record_id=daily_record.id,
            ingredient_id=ingredient.id,
            snapshot_type=SnapshotType.CLOSE,
            quantity=Decimal("15.0"),
        )
        db_session.commit()

        # Act
        summary = daily_operations_service.get_day_summary(db_session, daily_record.id)

        # Assert
        assert summary is not None

        # Both times should be strings (not datetime objects)
        assert isinstance(summary.opening_time, str)
        assert isinstance(summary.closing_time, str)

        # Both should be parseable ISO format
        opening_parsed = datetime.fromisoformat(summary.opening_time)
        closing_parsed = datetime.fromisoformat(summary.closing_time)

        # Verify times match original values
        assert opening_parsed.hour == 10
        assert opening_parsed.minute == 0
        assert closing_parsed.hour == 21
        assert closing_parsed.minute == 30

    def test_iso_format_does_not_cause_range_error_values(self, db_session: Session):
        """
        Given: A daily record with edge-case times (midnight, end of day)
        When: Getting day summary
        Then: Times should still be valid ISO format (no RangeError-causing values)

        This test ensures times like "00:00" or "23:59:59" are properly formatted.
        """
        # Arrange
        ingredient = build_ingredient(db_session, name="Test Ingredient 5")
        daily_record = build_daily_record(
            db_session,
            record_date=date(2024, 1, 17),
            status=DayStatus.CLOSED,
            opened_at=datetime(2024, 1, 17, 0, 0, 0),  # Midnight
            closed_at=datetime(2024, 1, 17, 23, 59, 59),  # End of day
        )
        build_inventory_snapshot(
            db_session,
            daily_record_id=daily_record.id,
            ingredient_id=ingredient.id,
            snapshot_type=SnapshotType.OPEN,
            quantity=Decimal("10.0"),
        )
        build_inventory_snapshot(
            db_session,
            daily_record_id=daily_record.id,
            ingredient_id=ingredient.id,
            snapshot_type=SnapshotType.CLOSE,
            quantity=Decimal("5.0"),
        )
        db_session.commit()

        # Act
        summary = daily_operations_service.get_day_summary(db_session, daily_record.id)

        # Assert
        assert summary is not None

        # Parse and verify edge case times
        opening_parsed = datetime.fromisoformat(summary.opening_time)
        closing_parsed = datetime.fromisoformat(summary.closing_time)

        assert opening_parsed.hour == 0
        assert opening_parsed.minute == 0
        assert closing_parsed.hour == 23
        assert closing_parsed.minute == 59
        assert closing_parsed.second == 59
