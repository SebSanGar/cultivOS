"""Shared test fixtures for cultivOS."""

import os
import pytest

os.environ["DB_URL"] = "sqlite:///:memory:"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"


@pytest.fixture
def db():
    """In-memory SQLite session for tests."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from cultivos.db.models import Base

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def app():
    """Create a fresh app instance for testing."""
    from cultivos.config import get_settings
    get_settings.cache_clear()
    from cultivos.app import create_app
    return create_app()


@pytest.fixture
def client(app, db):
    """HTTP test client with in-memory DB injected."""
    from fastapi.testclient import TestClient
    from cultivos.db.session import get_db

    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()
