"""
Tests for Bug Fix 2: Transaction API category_id null check.

Bug Description:
- Creating a revenue transaction (without category) caused AttributeError
- The code was accessing t.category.name without checking if category_id exists
- Fix added check: `t.category.name if t.category_id and t.category else None`

Test Scenarios:
- Create revenue transaction without category (should not error)
- Create expense transaction with category (category_name should be set)
- List transactions includes both with and without categories
"""

import pytest
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.transaction import TransactionType, PaymentMethod

from tests.builders import (
    build_expense_category,
    build_transaction,
)


class TestTransactionApiCategoryNull:
    """Tests for transaction API handling null category (Bug 2 fix)."""

    def test_create_revenue_transaction_without_category(self, client: TestClient, db_session: Session):
        """
        Given: A request to create a revenue transaction without a category
        When: POST /api/v1/transactions
        Then: Transaction should be created successfully with category_name as None
        """
        # Arrange
        payload = {
            "type": "revenue",
            "amount": "150.00",
            "payment_method": "cash",
            "transaction_date": str(date.today()),
            "description": "Sprzedaz dzienna",
            # Note: No category_id - revenue doesn't require category
        }

        # Act
        response = client.post("/api/v1/transactions", json=payload)

        # Assert
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

        data = response.json()
        assert data["type"] == "revenue"
        assert data["amount"] == "150.00"
        assert data["category_id"] is None
        assert data["category_name"] is None  # Bug fix: should be None, not AttributeError

    def test_create_expense_transaction_with_category(self, client: TestClient, db_session: Session):
        """
        Given: A request to create an expense transaction with a valid category
        When: POST /api/v1/transactions
        Then: Transaction should be created with category_name populated
        """
        # Arrange - need to create a level 3 (leaf) category for expenses
        level1 = build_expense_category(db_session, name="Koszty operacyjne", level=1)
        db_session.flush()
        level2 = build_expense_category(db_session, name="Skladniki", level=2, parent_id=level1.id)
        db_session.flush()
        level3 = build_expense_category(db_session, name="Mieso", level=3, parent_id=level2.id)
        db_session.commit()

        payload = {
            "type": "expense",
            "amount": "200.00",
            "payment_method": "bank_transfer",
            "transaction_date": str(date.today()),
            "category_id": level3.id,
            "description": "Zakup miesa",
        }

        # Act
        response = client.post("/api/v1/transactions", json=payload)

        # Assert
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

        data = response.json()
        assert data["type"] == "expense"
        assert data["category_id"] == level3.id
        assert data["category_name"] == "Mieso"

    def test_get_transaction_without_category_returns_null_category_name(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: A revenue transaction without category exists in the database
        When: GET /api/v1/transactions/{id}
        Then: Response should have category_name as None
        """
        # Arrange
        transaction = build_transaction(
            db_session,
            transaction_type=TransactionType.REVENUE,
            amount=Decimal("300.00"),
            payment_method=PaymentMethod.CARD,
            category_id=None,  # No category
            description="Platnosc kartowa",
        )
        db_session.commit()

        # Act
        response = client.get(f"/api/v1/transactions/{transaction.id}")

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == transaction.id
        assert data["category_id"] is None
        assert data["category_name"] is None  # Bug fix verification

    def test_list_transactions_with_mixed_categories(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: Database has transactions with and without categories
        When: GET /api/v1/transactions
        Then: All transactions should be returned, some with category_name, some with None
        """
        # Arrange
        category = build_expense_category(db_session, name="Oplaty", level=1)

        # Transaction with category
        build_transaction(
            db_session,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal("100.00"),
            payment_method=PaymentMethod.BANK_TRANSFER,
            category_id=category.id,
            description="Czynsz",
        )

        # Transaction without category (revenue)
        build_transaction(
            db_session,
            transaction_type=TransactionType.REVENUE,
            amount=Decimal("500.00"),
            payment_method=PaymentMethod.CASH,
            category_id=None,
            description="Sprzedaz",
        )

        db_session.commit()

        # Act
        response = client.get("/api/v1/transactions")

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 2

        items = data["items"]
        assert len(items) == 2

        # Verify both types are handled correctly
        expense_item = next(i for i in items if i["type"] == "expense")
        revenue_item = next(i for i in items if i["type"] == "revenue")

        assert expense_item["category_name"] == "Oplaty"
        assert revenue_item["category_name"] is None  # Bug fix: no error for null category

    def test_update_transaction_removing_category(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: An expense transaction with a category
        When: Updating to remove the category (set to null)
        Then: Update should succeed and category_name should be None
        """
        # Arrange
        category = build_expense_category(db_session, name="Temp Category", level=1)
        transaction = build_transaction(
            db_session,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal("50.00"),
            payment_method=PaymentMethod.CASH,
            category_id=category.id,
        )
        db_session.commit()

        payload = {
            "category_id": None,  # Remove category
        }

        # Act
        response = client.put(f"/api/v1/transactions/{transaction.id}", json=payload)

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert data["category_id"] is None
        assert data["category_name"] is None

    def test_filter_transactions_by_type_revenue(
        self, client: TestClient, db_session: Session
    ):
        """
        Given: Mixed transaction types in database
        When: GET /api/v1/transactions?type_filter=revenue
        Then: Only revenue transactions returned, all with category_name handling
        """
        # Arrange
        category = build_expense_category(db_session, name="Test", level=1)

        build_transaction(
            db_session,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal("100.00"),
            payment_method=PaymentMethod.CASH,
            category_id=category.id,
        )
        build_transaction(
            db_session,
            transaction_type=TransactionType.REVENUE,
            amount=Decimal("200.00"),
            payment_method=PaymentMethod.CARD,
            category_id=None,
        )
        build_transaction(
            db_session,
            transaction_type=TransactionType.REVENUE,
            amount=Decimal("300.00"),
            payment_method=PaymentMethod.CASH,
            category_id=None,
        )
        db_session.commit()

        # Act
        response = client.get("/api/v1/transactions?type_filter=revenue")

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 2

        for item in data["items"]:
            assert item["type"] == "revenue"
            assert item["category_name"] is None  # Revenue typically has no category
