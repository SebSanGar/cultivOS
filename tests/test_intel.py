"""Tests for intelligence dashboard API — cross-farm analytics."""

import os
import pytest
from datetime import datetime, timedelta


@pytest.fixture(autouse=True)
def enable_auth():
    """Intel tests need auth enabled for role checks."""
    os.environ["AUTH_ENABLED"] = "true"
    from cultivos.config import get_settings
    get_settings.cache_clear()
    yield
    os.environ.pop("AUTH_ENABLED", None)
    get_settings.cache_clear()


@pytest.fixture
def admin_token(client, db):
    """Register admin and return token."""
    # Admin users created directly in DB (admin self-registration blocked)
    from cultivos.db.models import User
    from cultivos.auth import hash_password
    # admin user created directly in DB


    if not db.query(User).filter(User.username == "inteladmin").first():
        db.add(User(username="inteladmin", hashed_password=hash_password("secret123"), role="admin"))
        db.commit()
    resp = client.post("/api/auth/login", json={
        "username": "inteladmin", "password": "secret123"
    })
    return resp.json()["access_token"]


@pytest.fixture
def admin_h(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def researcher_token(client):
    """Register researcher and return token."""
    client.post("/api/auth/register", json={
        "username": "intelresearcher", "password": "secret123", "role": "researcher"
    })
    resp = client.post("/api/auth/login", json={
        "username": "intelresearcher", "password": "secret123"
    })
    return resp.json()["access_token"]


@pytest.fixture
def researcher_h(researcher_token):
    return {"Authorization": f"Bearer {researcher_token}"}


@pytest.fixture
def farmer_token(client):
    """Register farmer and return token."""
    client.post("/api/auth/register", json={
        "username": "intelfarmer", "password": "secret123", "role": "farmer"
    })
    resp = client.post("/api/auth/login", json={
        "username": "intelfarmer", "password": "secret123"
    })
    return resp.json()["access_token"]


@pytest.fixture
def farmer_h(farmer_token):
    return {"Authorization": f"Bearer {farmer_token}"}


@pytest.fixture
def seed_data(db):
    """Create 2 farms, 3 fields, health scores, soil analyses, treatments."""
    from cultivos.db.models import (
        Farm, Field, HealthScore, SoilAnalysis, TreatmentRecord,
    )

    # Farm 1 with 2 fields
    farm1 = Farm(name="Rancho Uno", owner_name="Juan", location_lat=20.6,
                 location_lon=-103.3, total_hectares=50, municipality="Zapopan",
                 state="Jalisco", country="MX")
    db.add(farm1)
    db.flush()

    field1 = Field(farm_id=farm1.id, name="Parcela A", crop_type="maiz", hectares=20)
    field2 = Field(farm_id=farm1.id, name="Parcela B", crop_type="agave", hectares=30)
    db.add_all([field1, field2])
    db.flush()

    # Farm 2 with 1 field
    farm2 = Farm(name="Rancho Dos", owner_name="Pedro", location_lat=20.7,
                 location_lon=-103.4, total_hectares=25, municipality="Tlaquepaque",
                 state="Jalisco", country="MX")
    db.add(farm2)
    db.flush()

    field3 = Field(farm_id=farm2.id, name="Parcela C", crop_type="aguacate", hectares=25)
    db.add(field3)
    db.flush()

    now = datetime.utcnow()

    # Health scores for field1: declining (80 -> 65 -> 50)
    for i, score in enumerate([80.0, 65.0, 50.0]):
        hs = HealthScore(
            field_id=field1.id, score=score, trend="declining" if i > 0 else "stable",
            sources=["ndvi", "soil"], breakdown={"ndvi": score, "soil": score},
            scored_at=now - timedelta(days=30 * (2 - i)),
        )
        db.add(hs)

    # Health scores for field2: stable (70 -> 72)
    for i, score in enumerate([70.0, 72.0]):
        hs = HealthScore(
            field_id=field2.id, score=score, trend="stable",
            sources=["ndvi"], breakdown={"ndvi": score},
            scored_at=now - timedelta(days=30 * (1 - i)),
        )
        db.add(hs)

    # Health scores for field3: improving (40 -> 55)
    for i, score in enumerate([40.0, 55.0]):
        hs = HealthScore(
            field_id=field3.id, score=score,
            trend="improving" if i > 0 else "declining",
            sources=["ndvi", "soil"], breakdown={"ndvi": score, "soil": score},
            scored_at=now - timedelta(days=30 * (1 - i)),
        )
        db.add(hs)

    # Soil analyses at different times
    for i, (fid, ph, om) in enumerate([
        (field1.id, 6.5, 3.0),
        (field1.id, 6.8, 3.5),
        (field2.id, 7.0, 2.5),
        (field3.id, 5.5, 4.0),
    ]):
        sa = SoilAnalysis(
            field_id=fid, ph=ph, organic_matter_pct=om,
            nitrogen_ppm=20, phosphorus_ppm=15, potassium_ppm=100,
            sampled_at=now - timedelta(days=60 - i * 20),
        )
        db.add(sa)

    # Treatment for field1 (applied when health was 65)
    tr = TreatmentRecord(
        field_id=field1.id, health_score_used=65.0,
        problema="Bajo vigor vegetativo", causa_probable="Deficiencia de nitrogeno",
        tratamiento="Aplicar te de composta", costo_estimado_mxn=500,
        urgencia="media", prevencion="Rotacion con leguminosas",
        organic=True,
    )
    db.add(tr)

    db.commit()
    return {"farm1": farm1, "farm2": farm2, "field1": field1, "field2": field2, "field3": field3}


class TestIntelAllFarmsSummary:
    def test_intel_all_farms_summary(self, client, db, admin_h, seed_data):
        """GET /api/intel/summary -> total_farms, total_fields, avg_health, worst_field"""
        resp = client.get("/api/intel/summary", headers=admin_h)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_farms"] == 2
        assert data["total_fields"] == 3
        # avg_health = average of latest scores: field1=50, field2=72, field3=55 -> 59.0
        assert abs(data["avg_health"] - 59.0) < 0.5
        # worst_field = field1 with score 50
        assert data["worst_field"]["field_name"] == "Parcela A"
        assert data["worst_field"]["score"] == 50.0


class TestIntelSoilTrends:
    def test_intel_soil_trends(self, client, db, admin_h, seed_data):
        """GET /api/intel/soil-trends -> pH and organic_matter averages over time"""
        resp = client.get("/api/intel/soil-trends", headers=admin_h)
        assert resp.status_code == 200
        data = resp.json()
        assert "trends" in data
        assert len(data["trends"]) > 0
        # Each trend entry has date, avg_ph, avg_organic_matter
        entry = data["trends"][0]
        assert "date" in entry
        assert "avg_ph" in entry
        assert "avg_organic_matter" in entry


class TestIntelTreatmentEffectiveness:
    def test_intel_treatment_effectiveness(self, client, db, admin_h, seed_data):
        """GET /api/intel/treatments -> treatments applied + health score delta"""
        resp = client.get("/api/intel/treatments", headers=admin_h)
        assert resp.status_code == 200
        data = resp.json()
        assert "treatments" in data
        assert len(data["treatments"]) >= 1
        tr = data["treatments"][0]
        assert "field_name" in tr
        assert "tratamiento" in tr
        assert "health_before" in tr
        assert "health_after" in tr
        assert "delta" in tr


class TestIntelAnomalies:
    def test_intel_anomalies(self, client, db, admin_h, seed_data):
        """GET /api/intel/anomalies -> fields with health declining 2+ consecutive readings"""
        resp = client.get("/api/intel/anomalies", headers=admin_h)
        assert resp.status_code == 200
        data = resp.json()
        assert "anomalies" in data
        # field1 has 80->65->50 (declining 2 consecutive times)
        anomaly_fields = [a["field_name"] for a in data["anomalies"]]
        assert "Parcela A" in anomaly_fields


class TestIntelRequiresAdminOrResearcher:
    def test_farmer_gets_403(self, client, db, farmer_h, seed_data):
        """farmer role -> 403 on all intel endpoints"""
        for path in ["/api/intel/summary", "/api/intel/soil-trends",
                     "/api/intel/treatments", "/api/intel/anomalies"]:
            resp = client.get(path, headers=farmer_h)
            assert resp.status_code == 403, f"{path} should be 403 for farmer"

    def test_researcher_can_access(self, client, db, researcher_h, seed_data):
        """researcher role -> 200 on intel endpoints"""
        resp = client.get("/api/intel/summary", headers=researcher_h)
        assert resp.status_code == 200
