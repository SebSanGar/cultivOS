"""Tests for the data completeness dashboard at /completitud."""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Farm, Field, NDVIResult, SoilAnalysis, ThermalResult, WeatherRecord
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


def _seed_completeness_data(db):
    """Seed farm with partial data coverage for completeness testing."""
    farm = Farm(name="Finca Completitud", state="Jalisco", total_hectares=50.0)
    db.add(farm)
    db.flush()
    field = Field(
        farm_id=farm.id, name="Parcela A", hectares=15.0,
        crop_type="maiz", planted_at=datetime(2026, 3, 1),
    )
    db.add(field)
    db.flush()
    # Only add soil + NDVI (3 sources missing: thermal, treatments, weather)
    db.add(SoilAnalysis(field_id=field.id, ph=6.5, sampled_at=datetime.utcnow()))
    db.add(NDVIResult(
        field_id=field.id, ndvi_mean=0.7, ndvi_std=0.1,
        ndvi_min=0.3, ndvi_max=0.9, pixels_total=1000,
        stress_pct=10, zones=[], analyzed_at=datetime.utcnow(),
    ))
    db.commit()
    return farm, field


# -- Page Load Tests --


class TestCompletitudPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/completitud")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/completitud")
        assert "Completitud de Datos" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/completitud")
        assert 'id="comp-farm-select"' in resp.text

    def test_page_has_empty_state(self, client):
        resp = client.get("/completitud")
        assert 'id="comp-empty"' in resp.text

    def test_page_has_content_container(self, client):
        resp = client.get("/completitud")
        assert 'id="comp-content"' in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/completitud")
        assert 'id="comp-stats"' in resp.text

    def test_page_has_sources_grid(self, client):
        resp = client.get("/completitud")
        assert 'id="comp-sources"' in resp.text

    def test_page_has_recommendations_section(self, client):
        resp = client.get("/completitud")
        assert 'id="comp-recommendations"' in resp.text

    def test_page_has_js_script(self, client):
        resp = client.get("/completitud")
        assert "completitud.js" in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/completitud")
        assert "intel-nav" in resp.text

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/completitud")
        assert "Seleccione una granja" in resp.text


# -- API Integration Tests --


class TestCompletenessAPI:
    """Data completeness API returns expected data structure."""

    def test_api_returns_farm_score(self, client, db):
        farm, field = _seed_completeness_data(db)
        resp = client.get(f"/api/farms/{farm.id}/data-completeness")
        assert resp.status_code == 200
        data = resp.json()
        assert "farm_score" in data
        # 2 out of 5 sources = 40%
        assert data["farm_score"] == 40.0

    def test_api_returns_field_breakdown(self, client, db):
        farm, field = _seed_completeness_data(db)
        resp = client.get(f"/api/farms/{farm.id}/data-completeness")
        data = resp.json()
        assert len(data["fields"]) == 1
        f = data["fields"][0]
        assert f["has_soil"] is True
        assert f["has_ndvi"] is True
        assert f["has_thermal"] is False
        assert f["has_treatments"] is False

    def test_api_404_for_missing_farm(self, client):
        resp = client.get("/api/farms/9999/data-completeness")
        assert resp.status_code == 404

    def test_api_empty_farm_returns_zero(self, client, db):
        farm = Farm(name="Vacia", state="Jalisco", total_hectares=10.0)
        db.add(farm)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/data-completeness")
        assert resp.status_code == 200
        assert resp.json()["farm_score"] == 0.0

    def test_api_full_coverage_returns_100(self, client, db):
        farm = Farm(name="Completa", state="Jalisco", total_hectares=20.0)
        db.add(farm)
        db.flush()
        field = Field(farm_id=farm.id, name="Campo Full", hectares=10.0, crop_type="maiz")
        db.add(field)
        db.flush()
        from cultivos.db.models import TreatmentRecord
        db.add(SoilAnalysis(field_id=field.id, ph=7.0, sampled_at=datetime.utcnow()))
        db.add(NDVIResult(field_id=field.id, ndvi_mean=0.8, ndvi_std=0.05, ndvi_min=0.5, ndvi_max=0.95, pixels_total=500, stress_pct=5, zones=[], analyzed_at=datetime.utcnow()))
        db.add(ThermalResult(field_id=field.id, temp_mean=27, temp_std=2, temp_min=22, temp_max=33, pixels_total=500, stress_pct=8, analyzed_at=datetime.utcnow()))
        db.add(TreatmentRecord(field_id=field.id, health_score_used=80.0, problema="test", causa_probable="test", tratamiento="compost", urgencia="baja", prevencion="rotacion", organic=True))
        db.add(WeatherRecord(farm_id=farm.id, temp_c=25, humidity_pct=60, wind_kmh=10, rainfall_mm=0, description="clear"))
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/data-completeness")
        assert resp.json()["farm_score"] == 100.0
