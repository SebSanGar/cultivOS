"""Tests for the global data completeness dashboard at /completitud-global."""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import (
    Farm, Field, NDVIResult, SoilAnalysis, ThermalResult,
    TreatmentRecord, WeatherRecord,
)
from cultivos.db.session import get_db


@pytest.fixture()
def app(db):
    application = create_app()
    application.dependency_overrides[get_db] = lambda: db
    yield application
    application.dependency_overrides.clear()


@pytest.fixture()
def client(app):
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def admin_headers(client, db):
    """Register admin user and return auth headers."""
    from cultivos.db.models import User
    from cultivos.auth import hash_password

    if not db.query(User).filter(User.username == "testadmin").first():
        db.add(User(username="testadmin", hashed_password=hash_password("secret123"), role="admin"))
        db.commit()
    resp = client.post("/api/auth/login", json={
        "username": "testadmin", "password": "secret123"
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _seed_two_farms(db):
    """Seed two farms with varying data completeness."""
    farm1 = Farm(name="Finca Completa", state="Jalisco", total_hectares=30.0)
    farm2 = Farm(name="Finca Incompleta", state="Michoacan", total_hectares=20.0)
    db.add_all([farm1, farm2])
    db.flush()

    f1 = Field(farm_id=farm1.id, name="Parcela A", hectares=10.0,
               crop_type="maiz", planted_at=datetime(2026, 2, 1))
    f2 = Field(farm_id=farm2.id, name="Parcela B", hectares=8.0,
               crop_type="agave", planted_at=datetime(2026, 3, 1))
    db.add_all([f1, f2])
    db.flush()

    # Farm 1 has all data types
    db.add(SoilAnalysis(field_id=f1.id, ph=6.5, organic_matter_pct=3.2, sampled_at=datetime(2026, 2, 5)))
    db.add(NDVIResult(
        field_id=f1.id, ndvi_mean=0.72, ndvi_std=0.05, ndvi_min=0.4,
        ndvi_max=0.9, pixels_total=1000, stress_pct=5.0, zones=[],
        analyzed_at=datetime(2026, 2, 10),
    ))
    db.add(ThermalResult(
        field_id=f1.id, temp_mean=28.5, temp_std=2.0, temp_min=24.0,
        temp_max=33.0, pixels_total=1000, stress_pct=10.0,
        irrigation_deficit=False, analyzed_at=datetime(2026, 2, 10),
    ))
    db.add(TreatmentRecord(
        field_id=f1.id, health_score_used=60.0, problema="Bajo vigor",
        causa_probable="Suelo pobre", tratamiento="Composta 3 ton/ha",
        costo_estimado_mxn=1500, urgencia="media", prevencion="Rotacion",
        organic=True, applied_at=datetime(2026, 2, 15),
    ))
    db.add(WeatherRecord(
        farm_id=farm1.id, recorded_at=datetime(2026, 2, 10),
        temp_c=28.0, humidity_pct=65.0, wind_kmh=12.0, rainfall_mm=0.0,
        description="Soleado",
    ))

    # Farm 2 has only soil
    db.add(SoilAnalysis(field_id=f2.id, ph=5.8, organic_matter_pct=2.1, sampled_at=datetime(2026, 3, 5)))
    db.commit()
    return farm1, farm2, f1, f2


# -- Page Load Tests --


class TestCompletitudGlobalPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/completitud-global")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/completitud-global")
        assert "Completitud Global" in resp.text

    def test_page_has_table_container(self, client):
        resp = client.get("/completitud-global")
        assert 'id="cg-table-container"' in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/completitud-global")
        assert 'id="cg-stats"' in resp.text

    def test_page_has_js_script(self, client):
        resp = client.get("/completitud-global")
        assert "completitud-global.js" in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/completitud-global")
        assert "intel-nav" in resp.text

    def test_page_has_empty_state(self, client):
        resp = client.get("/completitud-global")
        assert 'id="cg-empty"' in resp.text

    def test_page_has_footer(self, client):
        resp = client.get("/completitud-global")
        assert "cultivos-footer" in resp.text

    def test_page_has_state_filter(self, client):
        resp = client.get("/completitud-global")
        assert 'id="cg-state-filter"' in resp.text

    def test_page_subtitle_mentions_datos(self, client):
        resp = client.get("/completitud-global")
        assert "datos" in resp.text.lower()


# -- API Integration Tests --


class TestCompletitudGlobalAPI:
    """Global data completeness API works correctly."""

    def test_api_returns_200(self, client, db, admin_headers):
        resp = client.get("/api/intel/data-completeness-global", headers=admin_headers)
        assert resp.status_code == 200

    def test_api_returns_farms_list(self, client, db, admin_headers):
        _seed_two_farms(db)
        resp = client.get("/api/intel/data-completeness-global", headers=admin_headers)
        data = resp.json()
        assert "farms" in data
        assert len(data["farms"]) == 2

    def test_api_farm_has_expected_fields(self, client, db, admin_headers):
        _seed_two_farms(db)
        resp = client.get("/api/intel/data-completeness-global", headers=admin_headers)
        farm = resp.json()["farms"][0]
        assert "farm_id" in farm
        assert "farm_name" in farm
        assert "farm_score" in farm
        assert "has_soil" in farm
        assert "has_ndvi" in farm
        assert "has_thermal" in farm
        assert "has_treatments" in farm
        assert "has_weather" in farm

    def test_api_complete_farm_has_high_score(self, client, db, admin_headers):
        _seed_two_farms(db)
        resp = client.get("/api/intel/data-completeness-global", headers=admin_headers)
        farms = resp.json()["farms"]
        # Find Finca Completa
        completa = next(f for f in farms if f["farm_name"] == "Finca Completa")
        assert completa["farm_score"] == 100.0

    def test_api_incomplete_farm_has_low_score(self, client, db, admin_headers):
        _seed_two_farms(db)
        resp = client.get("/api/intel/data-completeness-global", headers=admin_headers)
        farms = resp.json()["farms"]
        incompleta = next(f for f in farms if f["farm_name"] == "Finca Incompleta")
        assert incompleta["farm_score"] < 50.0

    def test_api_has_summary_stats(self, client, db, admin_headers):
        _seed_two_farms(db)
        resp = client.get("/api/intel/data-completeness-global", headers=admin_headers)
        data = resp.json()
        assert "total_farms" in data
        assert "avg_score" in data
        assert data["total_farms"] == 2

    def test_api_empty_no_farms(self, client, db, admin_headers):
        resp = client.get("/api/intel/data-completeness-global", headers=admin_headers)
        data = resp.json()
        assert data["farms"] == []
        assert data["total_farms"] == 0

    def test_api_state_filter(self, client, db, admin_headers):
        _seed_two_farms(db)
        resp = client.get(
            "/api/intel/data-completeness-global",
            params={"state": "Jalisco"},
            headers=admin_headers,
        )
        data = resp.json()
        assert data["total_farms"] == 1
        assert data["farms"][0]["farm_name"] == "Finca Completa"
