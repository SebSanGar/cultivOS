"""Tests for intel-level aggregate economic impact — card on intel page."""

from datetime import datetime

import pytest


@pytest.fixture
def researcher_headers(client):
    """Register a researcher user and return auth headers."""
    client.post("/api/auth/register", json={
        "username": "econresearcher", "password": "secret123", "role": "researcher"
    })
    resp = client.post("/api/auth/login", json={
        "username": "econresearcher", "password": "secret123"
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _seed_farms(db):
    """Create two farms with fields, health scores, and treatments."""
    from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord

    farm1 = Farm(
        name="Rancho Agave",
        owner_name="Carlos",
        state="Jalisco",
        location_lat=20.6,
        location_lon=-103.3,
    )
    farm2 = Farm(
        name="Rancho Berries",
        owner_name="Maria",
        state="Jalisco",
        location_lat=20.7,
        location_lon=-103.4,
    )
    db.add_all([farm1, farm2])
    db.commit()
    db.refresh(farm1)
    db.refresh(farm2)

    f1 = Field(farm_id=farm1.id, name="Parcela Norte", crop_type="agave", hectares=10.0)
    f2 = Field(farm_id=farm2.id, name="Parcela Sur", crop_type="berries", hectares=8.0)
    db.add_all([f1, f2])
    db.commit()
    db.refresh(f1)
    db.refresh(f2)

    hs1 = HealthScore(field_id=f1.id, score=80.0, trend="improving", sources=["ndvi"], breakdown={"ndvi": 80.0})
    hs2 = HealthScore(field_id=f2.id, score=65.0, trend="stable", sources=["ndvi"], breakdown={"ndvi": 65.0})
    db.add_all([hs1, hs2])

    tr1 = TreatmentRecord(
        field_id=f1.id, health_score_used=80.0,
        problema="Plaga", causa_probable="Humedad", tratamiento="Neem",
        prevencion="Rotacion", costo_estimado_mxn=300, urgencia="baja",
        applied_at=datetime.utcnow(),
    )
    db.add(tr1)
    db.commit()


class TestIntelEconomicsAPI:
    def test_economics_returns_aggregate(self, client, db, researcher_headers):
        """GET /api/intel/economics returns aggregate savings across all farms."""
        _seed_farms(db)
        resp = client.get("/api/intel/economics", headers=researcher_headers)
        assert resp.status_code == 200

        data = resp.json()
        assert "total_farms" in data
        assert "total_hectares" in data
        assert "total_savings_mxn" in data
        assert "water_savings_mxn" in data
        assert "fertilizer_savings_mxn" in data
        assert "yield_improvement_mxn" in data
        assert data["total_farms"] == 2
        assert data["total_hectares"] == 18.0
        assert data["total_savings_mxn"] > 0

    def test_economics_empty_no_farms(self, client, db, researcher_headers):
        """Returns zeros when no farms exist."""
        resp = client.get("/api/intel/economics", headers=researcher_headers)
        assert resp.status_code == 200

        data = resp.json()
        assert data["total_farms"] == 0
        assert data["total_savings_mxn"] == 0

    def test_economics_per_farm_breakdown(self, client, db, researcher_headers):
        """Response includes per-farm breakdown list."""
        _seed_farms(db)
        resp = client.get("/api/intel/economics", headers=researcher_headers)
        data = resp.json()

        assert "farms" in data
        assert len(data["farms"]) == 2
        for farm in data["farms"]:
            assert "farm_name" in farm
            assert "hectares" in farm
            assert "total_savings_mxn" in farm

    def test_economics_auth_dependency_present(self, client, db, researcher_headers):
        """Endpoint works with researcher auth headers."""
        resp = client.get("/api/intel/economics", headers=researcher_headers)
        assert resp.status_code == 200


class TestIntelEconomicsFrontend:
    def test_economics_card_in_html(self, client):
        """Intel page HTML includes economics container."""
        resp = client.get("/intel")
        assert resp.status_code == 200
        assert 'id="intel-economics"' in resp.text

    def test_economics_card_shows_title(self, client):
        """Economics card has the correct Spanish title."""
        resp = client.get("/intel")
        assert "Impacto Econ" in resp.text

    def test_economics_card_shows_currency(self, client):
        """Economics card labels reference MXN currency."""
        resp = client.get("/intel")
        assert "MXN" in resp.text
