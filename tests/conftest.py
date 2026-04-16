"""Shared test fixtures for cultivOS."""

import os
import pytest

os.environ["DB_URL"] = "sqlite:///:memory:"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["AUTH_ENABLED"] = "false"


@pytest.fixture(autouse=True)
def _auth_baseline():
    """Ensure AUTH_ENABLED=false and settings cache is fresh at the start of every test.

    Test modules that need auth enabled (test_auth.py, test_intel.py, etc.) use their
    own autouse fixtures to flip it to 'true'. This baseline fixture runs first in setup
    (conftest fixtures precede module fixtures) and last in teardown, so it always
    restores a clean auth-disabled state regardless of what the test changed.
    """
    from cultivos.config import get_settings
    os.environ["AUTH_ENABLED"] = "false"
    get_settings.cache_clear()
    yield
    os.environ["AUTH_ENABLED"] = "false"
    get_settings.cache_clear()


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


@pytest.fixture
def admin_headers(client, db):
    """Create an admin user directly in DB (API registration blocks admin role) and return auth headers."""
    from cultivos.db.models import User
    from cultivos.auth import hash_password
    existing = db.query(User).filter(User.username == "testadmin").first()
    if not existing:
        user = User(username="testadmin", hashed_password=hash_password("secret123"), role="admin")
        db.add(user)
        db.commit()
    resp = client.post("/api/auth/login", json={
        "username": "testadmin", "password": "secret123"
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
