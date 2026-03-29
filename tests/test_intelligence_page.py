"""Tests for the comprehensive field intelligence page at /inteligencia."""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import (
    Farm, Field, HealthScore, NDVIResult, ThermalResult,
    SoilAnalysis, MicrobiomeRecord, WeatherRecord, TreatmentRecord,
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


def _seed_full_data(db):
    """Seed farm, field, and ALL data sources for comprehensive intelligence."""
    farm = Farm(name="Rancho Cerebro", state="Jalisco", total_hectares=80.0)
    db.add(farm)
    db.flush()
    field = Field(
        farm_id=farm.id, name="Parcela Completa", hectares=25.0,
        crop_type="maiz", planted_at=datetime(2026, 1, 15),
    )
    db.add(field)
    db.flush()

    health = HealthScore(
        field_id=field.id, score=72.5, trend="improving",
        sources=["ndvi", "soil", "thermal"], breakdown={"ndvi": 75.0, "soil": 70.0, "thermal": 72.0},
        scored_at=datetime(2026, 3, 1),
    )
    ndvi = NDVIResult(
        field_id=field.id, ndvi_mean=0.65, ndvi_std=0.12, ndvi_min=0.3, ndvi_max=0.85,
        pixels_total=50000, stress_pct=15.0,
        zones=[{"zone": "norte", "mean": 0.6}],
    )
    thermal = ThermalResult(
        field_id=field.id, stress_pct=20.0, irrigation_deficit=False,
        temp_mean=28.0, temp_std=3.5, temp_min=22.0, temp_max=35.0,
        pixels_total=50000, analyzed_at=datetime(2026, 3, 1),
    )
    soil = SoilAnalysis(
        field_id=field.id, ph=6.5, organic_matter_pct=3.2,
        nitrogen_ppm=45.0, phosphorus_ppm=22.0, potassium_ppm=180.0,
        texture="franco", moisture_pct=35.0, depth_cm=30.0,
        sampled_at=datetime(2026, 2, 15),
    )
    micro = MicrobiomeRecord(
        field_id=field.id, respiration_rate=85.0, microbial_biomass_carbon=320.0,
        fungi_bacteria_ratio=1.2, classification="healthy",
        sampled_at=datetime(2026, 2, 20),
    )
    weather = WeatherRecord(
        farm_id=farm.id, temp_c=27.0, humidity_pct=65.0,
        wind_kmh=12.0, rainfall_mm=5.0, description="Parcialmente nublado",
        forecast_3day=[{"day": 1, "temp_c": 28.0}],
        recorded_at=datetime(2026, 3, 1),
    )
    treatment = TreatmentRecord(
        field_id=field.id, health_score_used=65.0,
        problema="Estres hidrico leve", causa_probable="Deficit de riego",
        tratamiento="Riego profundo 20mm", costo_estimado_mxn=500,
        urgencia="media", prevencion="Mulching organico", organic=True,
    )
    db.add_all([health, ndvi, thermal, soil, micro, weather, treatment])
    db.commit()
    return farm, field


def _seed_empty_farm(db):
    """Seed farm with field but no sensor/analysis data."""
    farm = Farm(name="Rancho Vacio", state="Jalisco", total_hectares=30.0)
    db.add(farm)
    db.flush()
    field = Field(
        farm_id=farm.id, name="Parcela Sin Datos", hectares=10.0, crop_type="frijol",
    )
    db.add(field)
    db.commit()
    return farm, field


class TestIntelligencePageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/inteligencia")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/inteligencia")
        assert "Inteligencia de Campo" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/inteligencia")
        assert 'id="intel-farm-select"' in resp.text

    def test_page_has_field_selector(self, client):
        resp = client.get("/inteligencia")
        assert 'id="intel-field-select"' in resp.text

    def test_page_has_load_button(self, client):
        resp = client.get("/inteligencia")
        assert "Consultar" in resp.text

    def test_page_has_empty_state(self, client):
        resp = client.get("/inteligencia")
        assert 'id="intel-page-empty"' in resp.text

    def test_page_has_content_container(self, client):
        resp = client.get("/inteligencia")
        assert 'id="intel-page-content"' in resp.text

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/inteligencia")
        html = resp.text
        assert "Seleccione una granja" in html
        assert "Seleccione un campo" in html

    def test_page_has_js_script(self, client):
        resp = client.get("/inteligencia")
        assert "intelligence-page.js" in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/inteligencia")
        assert "intel-nav" in resp.text


class TestIntelligencePageSections:
    """Page contains all 12 data section containers."""

    def test_has_health_section(self, client):
        resp = client.get("/inteligencia")
        assert 'id="intel-section-health"' in resp.text

    def test_has_ndvi_section(self, client):
        resp = client.get("/inteligencia")
        assert 'id="intel-section-ndvi"' in resp.text

    def test_has_thermal_section(self, client):
        resp = client.get("/inteligencia")
        assert 'id="intel-section-thermal"' in resp.text

    def test_has_soil_section(self, client):
        resp = client.get("/inteligencia")
        assert 'id="intel-section-soil"' in resp.text

    def test_has_microbiome_section(self, client):
        resp = client.get("/inteligencia")
        assert 'id="intel-section-microbiome"' in resp.text

    def test_has_weather_section(self, client):
        resp = client.get("/inteligencia")
        assert 'id="intel-section-weather"' in resp.text

    def test_has_growth_section(self, client):
        resp = client.get("/inteligencia")
        assert 'id="intel-section-growth"' in resp.text

    def test_has_disease_section(self, client):
        resp = client.get("/inteligencia")
        assert 'id="intel-section-disease"' in resp.text

    def test_has_yield_section(self, client):
        resp = client.get("/inteligencia")
        assert 'id="intel-section-yield"' in resp.text

    def test_has_treatments_section(self, client):
        resp = client.get("/inteligencia")
        assert 'id="intel-section-treatments"' in resp.text

    def test_has_carbon_section(self, client):
        resp = client.get("/inteligencia")
        assert 'id="intel-section-carbon"' in resp.text

    def test_has_fusion_section(self, client):
        resp = client.get("/inteligencia")
        assert 'id="intel-section-fusion"' in resp.text


class TestIntelligenceAPI:
    """Intelligence API returns expected data for seeded fields."""

    def test_intelligence_returns_200(self, client, db):
        farm, field = _seed_full_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/intelligence")
        assert resp.status_code == 200

    def test_intelligence_has_field_info(self, client, db):
        farm, field = _seed_full_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/intelligence")
        data = resp.json()
        assert data["field_name"] == "Parcela Completa"
        assert data["crop_type"] == "maiz"
        assert data["hectares"] == 25.0

    def test_intelligence_has_health(self, client, db):
        farm, field = _seed_full_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/intelligence")
        data = resp.json()
        assert data["health"] is not None
        assert data["health"]["score"] == 72.5
        assert data["health"]["trend"] == "improving"

    def test_intelligence_has_ndvi(self, client, db):
        farm, field = _seed_full_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/intelligence")
        data = resp.json()
        assert data["ndvi"] is not None
        assert data["ndvi"]["ndvi_mean"] == 0.65

    def test_intelligence_has_thermal(self, client, db):
        farm, field = _seed_full_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/intelligence")
        data = resp.json()
        assert data["thermal"] is not None
        assert data["thermal"]["temp_mean"] == 28.0

    def test_intelligence_has_soil(self, client, db):
        farm, field = _seed_full_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/intelligence")
        data = resp.json()
        assert data["soil"] is not None
        assert data["soil"]["ph"] == 6.5

    def test_intelligence_has_microbiome(self, client, db):
        farm, field = _seed_full_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/intelligence")
        data = resp.json()
        assert data["microbiome"] is not None
        assert data["microbiome"]["classification"] == "healthy"

    def test_intelligence_has_weather(self, client, db):
        farm, field = _seed_full_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/intelligence")
        data = resp.json()
        assert data["weather"] is not None
        assert data["weather"]["temp_c"] == 27.0

    def test_intelligence_has_growth_stage(self, client, db):
        farm, field = _seed_full_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/intelligence")
        data = resp.json()
        assert data["growth_stage"] is not None
        assert "stage" in data["growth_stage"]

    def test_intelligence_has_disease_risk(self, client, db):
        farm, field = _seed_full_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/intelligence")
        data = resp.json()
        assert data["disease_risk"] is not None
        assert "risk_level" in data["disease_risk"]

    def test_intelligence_has_yield(self, client, db):
        farm, field = _seed_full_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/intelligence")
        data = resp.json()
        assert data["yield_prediction"] is not None
        assert data["yield_prediction"]["kg_per_ha"] > 0

    def test_intelligence_has_treatments(self, client, db):
        farm, field = _seed_full_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/intelligence")
        data = resp.json()
        assert len(data["treatments"]) >= 1
        assert data["treatments"][0]["problema"] == "Estres hidrico leve"

    def test_intelligence_has_carbon(self, client, db):
        farm, field = _seed_full_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/intelligence")
        data = resp.json()
        assert data["carbon"] is not None
        assert data["carbon"]["soc_pct"] is not None

    def test_intelligence_has_fusion(self, client, db):
        farm, field = _seed_full_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/intelligence")
        data = resp.json()
        assert data["fusion"] is not None
        assert data["fusion"]["confidence"] > 0

    def test_intelligence_empty_field(self, client, db):
        farm, field = _seed_empty_farm(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/intelligence")
        assert resp.status_code == 200
        data = resp.json()
        assert data["health"] is None
        assert data["ndvi"] is None
        assert data["thermal"] is None
        assert data["soil"] is None

    def test_intelligence_404_missing_farm(self, client, db):
        resp = client.get("/api/farms/9999/fields/1/intelligence")
        assert resp.status_code == 404

    def test_intelligence_404_missing_field(self, client, db):
        farm, field = _seed_full_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/9999/intelligence")
        assert resp.status_code == 404


class TestIntelligencePageStats:
    """Page has stats strip with expected stat containers."""

    def test_has_health_stat(self, client):
        resp = client.get("/inteligencia")
        assert 'id="intel-stat-health"' in resp.text

    def test_has_ndvi_stat(self, client):
        resp = client.get("/inteligencia")
        assert 'id="intel-stat-ndvi"' in resp.text

    def test_has_risk_stat(self, client):
        resp = client.get("/inteligencia")
        assert 'id="intel-stat-risk"' in resp.text

    def test_has_treatments_stat(self, client):
        resp = client.get("/inteligencia")
        assert 'id="intel-stat-treatments"' in resp.text

    def test_has_fusion_stat(self, client):
        resp = client.get("/inteligencia")
        assert 'id="intel-stat-fusion"' in resp.text
