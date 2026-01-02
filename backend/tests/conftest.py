"""
Pytest configuration and shared fixtures for backend tests.

Uses session-scoped database engine with per-test transaction rollback
for optimal test performance.
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import Base, get_db
from app.api.deps import get_db as api_get_db


# Use in-memory SQLite for tests (fast, no external dependencies)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def db_engine():
    """
    Create database engine and schema ONCE per test session.

    Using StaticPool ensures the same connection is used for all operations
    in SQLite in-memory database (required for testing).
    """
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Enable SQLite foreign keys
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """
    Each test gets a transaction that rolls back automatically.

    This is much faster than recreating tables for each test.
    """
    connection = db_engine.connect()
    transaction = connection.begin()

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestingSessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    FastAPI test client with database session override.

    The same session is used for both the API and direct test queries,
    ensuring consistency within a single test.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Session is managed by the db_session fixture

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[api_get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
