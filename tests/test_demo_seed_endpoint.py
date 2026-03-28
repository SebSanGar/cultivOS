"""Tests for the POST /api/demo/seed endpoint and demo seeding via API."""

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Base, Farm, Field, HealthScore, NDVIResult


@pytest.fixture
def client(db):
    app = create_app()
    from cultivos.db.session import get_db
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app, raise_server_exceptions=False)


class TestDemoSeedEndpoint:
    """POST /api/demo/seed triggers demo data seeding."""

    def test_seed_returns_201_with_counts(self, client):
        resp = client.post("/api/demo/seed")
        assert resp.status_code == 201
        data = resp.json()
        assert data["farms"] == 3
        assert data["fields"] == 8  # 3+3+2

    def test_seed_creates_farms_in_db(self, client, db):
        client.post("/api/demo/seed")
        farms = db.query(Farm).filter(Farm.name.contains("[DEMO]")).all()
        assert len(farms) == 3

    def test_seed_creates_fields_with_data(self, client, db):
        client.post("/api/demo/seed")
        fields = db.query(Field).all()
        assert len(fields) == 8
        # Each field should have NDVI + health data
        for f in fields:
            assert db.query(NDVIResult).filter_by(field_id=f.id).count() >= 24
            assert db.query(HealthScore).filter_by(field_id=f.id).count() >= 24

    def test_seed_is_idempotent(self, client):
        resp1 = client.post("/api/demo/seed")
        assert resp1.status_code == 201
        resp2 = client.post("/api/demo/seed")
        assert resp2.status_code == 200
        assert resp2.json()["message"] == "Demo data already exists"

    def test_seed_idempotent_no_duplicates(self, client, db):
        client.post("/api/demo/seed")
        count1 = db.query(Farm).count()
        client.post("/api/demo/seed")
        count2 = db.query(Farm).count()
        assert count1 == count2

    def test_get_demo_farms_returns_seeded_data(self, client):
        client.post("/api/demo/seed")
        resp = client.get("/api/demo/farms")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        # Each farm should have fields
        for farm in data:
            assert len(farm["fields"]) >= 2
