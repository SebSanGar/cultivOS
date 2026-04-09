"""Tests for cooperative management — CRUD + dashboard aggregation."""

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Base, Farm, Field, HealthScore, Cooperative
from cultivos.db.session import get_db


@pytest.fixture
def client(db):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def sample_cooperative(db):
    """Create a cooperative with 2 member farms."""
    coop = Cooperative(
        name="Cooperativa Valles Centrales",
        state="Jalisco",
        contact_name="Maria Garcia",
        contact_phone="+5213312345678",
    )
    db.add(coop)
    db.flush()

    farm1 = Farm(
        name="Rancho Uno", state="Jalisco", total_hectares=50.0,
        cooperative_id=coop.id,
    )
    farm2 = Farm(
        name="Rancho Dos", state="Jalisco", total_hectares=30.0,
        cooperative_id=coop.id,
    )
    db.add_all([farm1, farm2])
    db.flush()

    f1 = Field(name="Milpa Norte", farm_id=farm1.id, crop_type="maiz", hectares=25.0)
    f2 = Field(name="Agave Sur", farm_id=farm2.id, crop_type="agave", hectares=15.0)
    db.add_all([f1, f2])
    db.flush()

    # Add health scores
    from datetime import datetime
    hs1 = HealthScore(field_id=f1.id, score=72, scored_at=datetime(2026, 4, 1))
    hs2 = HealthScore(field_id=f2.id, score=58, scored_at=datetime(2026, 4, 1))
    db.add_all([hs1, hs2])
    db.commit()

    return coop


class TestCooperativeCRUD:
    """POST/GET/PUT/DELETE /api/cooperatives."""

    def test_create_cooperative(self, client):
        resp = client.post("/api/cooperatives", json={
            "name": "Test Coop",
            "state": "Jalisco",
            "contact_name": "Juan Perez",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test Coop"
        assert data["state"] == "Jalisco"
        assert data["contact_name"] == "Juan Perez"
        assert "id" in data

    def test_create_cooperative_minimal(self, client):
        resp = client.post("/api/cooperatives", json={"name": "Minimal Coop"})
        assert resp.status_code == 201
        assert resp.json()["name"] == "Minimal Coop"

    def test_create_cooperative_missing_name(self, client):
        resp = client.post("/api/cooperatives", json={"state": "Jalisco"})
        assert resp.status_code == 422

    def test_list_cooperatives(self, client, sample_cooperative):
        resp = client.get("/api/cooperatives")
        assert resp.status_code == 200
        data = resp.json()
        assert data["meta"]["total"] >= 1
        assert len(data["data"]) >= 1
        coop = data["data"][0]
        assert coop["name"] == "Cooperativa Valles Centrales"
        assert coop["farm_count"] == 2

    def test_get_cooperative(self, client, sample_cooperative):
        resp = client.get(f"/api/cooperatives/{sample_cooperative.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Cooperativa Valles Centrales"
        assert data["farm_count"] == 2

    def test_get_cooperative_not_found(self, client):
        resp = client.get("/api/cooperatives/9999")
        assert resp.status_code == 404

    def test_update_cooperative(self, client, sample_cooperative):
        resp = client.put(f"/api/cooperatives/{sample_cooperative.id}", json={
            "name": "Coop Actualizada",
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "Coop Actualizada"

    def test_update_cooperative_not_found(self, client):
        resp = client.put("/api/cooperatives/9999", json={"name": "X"})
        assert resp.status_code == 404

    def test_delete_cooperative(self, client, sample_cooperative):
        resp = client.delete(f"/api/cooperatives/{sample_cooperative.id}")
        assert resp.status_code == 204
        # Verify deleted
        resp2 = client.get(f"/api/cooperatives/{sample_cooperative.id}")
        assert resp2.status_code == 404


class TestCooperativeDashboard:
    """GET /api/cooperatives/{id}/dashboard — aggregate stats across member farms."""

    def test_dashboard_returns_aggregates(self, client, sample_cooperative):
        resp = client.get(f"/api/cooperatives/{sample_cooperative.id}/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["cooperative_id"] == sample_cooperative.id
        assert data["cooperative_name"] == "Cooperativa Valles Centrales"
        assert data["total_farms"] == 2
        assert data["total_fields"] == 2
        assert data["total_hectares"] == 80.0  # 50 + 30
        assert data["avg_health"] is not None
        assert 58 <= data["avg_health"] <= 72  # average of 72 and 58

    def test_dashboard_not_found(self, client):
        resp = client.get("/api/cooperatives/9999/dashboard")
        assert resp.status_code == 404

    def test_dashboard_empty_cooperative(self, client, db):
        """Cooperative with no farms returns zero stats."""
        coop = Cooperative(name="Empty Coop", state="Jalisco")
        db.add(coop)
        db.commit()
        resp = client.get(f"/api/cooperatives/{coop.id}/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_farms"] == 0
        assert data["total_fields"] == 0
        assert data["total_hectares"] == 0
        assert data["avg_health"] is None

    def test_dashboard_includes_farm_list(self, client, sample_cooperative):
        resp = client.get(f"/api/cooperatives/{sample_cooperative.id}/dashboard")
        data = resp.json()
        assert "farms" in data
        assert len(data["farms"]) == 2
        farm_names = {f["name"] for f in data["farms"]}
        assert "Rancho Uno" in farm_names
        assert "Rancho Dos" in farm_names


class TestCooperativaPage:
    """Frontend page at /cooperativa."""

    def test_page_loads(self, client):
        resp = client.get("/cooperativa")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_page_has_key_elements(self, client):
        resp = client.get("/cooperativa")
        html = resp.text
        assert "Cooperativas" in html or "cooperativa" in html.lower()

    def test_page_has_container(self, client):
        resp = client.get("/cooperativa")
        html = resp.text
        assert "coopList" in html or "coop-list" in html
