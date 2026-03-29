"""Tests for the irrigation scheduling page at /riego."""

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Farm, Field, SoilAnalysis, ThermalResult, WeatherRecord
from cultivos.db.session import get_db

from datetime import datetime


@pytest.fixture()
def app(db):
    application = create_app()
    application.dependency_overrides[get_db] = lambda: db
    yield application
    application.dependency_overrides.clear()


@pytest.fixture()
def client(app):
    return TestClient(app, raise_server_exceptions=False)


def _seed_irrigation_data(db):
    """Seed farm with field, soil, weather, and thermal data for irrigation."""
    farm = Farm(name="Rancho Riego", state="Jalisco", total_hectares=80.0)
    db.add(farm)
    db.flush()
    field = Field(
        farm_id=farm.id, name="Parcela Irrigada", hectares=25.0, crop_type="maiz",
    )
    db.add(field)
    db.flush()
    soil = SoilAnalysis(
        field_id=field.id, texture="clay_loam", moisture_pct=22.0,
        ph=6.5, organic_matter_pct=3.2,
        sampled_at=datetime(2026, 3, 1),
    )
    weather = WeatherRecord(
        farm_id=farm.id, temp_c=32.0, humidity_pct=40.0, rainfall_mm=2.0,
        wind_kmh=12.0, description="Parcialmente nublado", forecast_3day=[],
        recorded_at=datetime(2026, 3, 1),
    )
    thermal = ThermalResult(
        field_id=field.id, stress_pct=35.0, irrigation_deficit=True,
        temp_mean=28.5, temp_std=3.2, temp_min=22.0, temp_max=38.0,
        pixels_total=50000, analyzed_at=datetime(2026, 3, 1),
    )
    db.add_all([soil, weather, thermal])
    db.commit()
    return farm, field


def _seed_empty_farm(db):
    """Seed farm with field but no soil/weather/thermal data."""
    farm = Farm(name="Rancho Seco", state="Jalisco", total_hectares=30.0)
    db.add(farm)
    db.flush()
    field = Field(
        farm_id=farm.id, name="Parcela Vacia", hectares=10.0, crop_type="frijol",
    )
    db.add(field)
    db.commit()
    return farm, field


class TestIrrigationPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/riego")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/riego")
        assert "Riego" in resp.text or "riego" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/riego")
        assert 'id="irrigation-farm-select"' in resp.text

    def test_page_has_field_selector(self, client):
        resp = client.get("/riego")
        assert 'id="irrigation-field-select"' in resp.text

    def test_page_has_load_button(self, client):
        resp = client.get("/riego")
        assert "Consultar" in resp.text

    def test_page_has_empty_state(self, client):
        resp = client.get("/riego")
        assert 'id="irrigation-empty"' in resp.text

    def test_page_has_schedule_container(self, client):
        resp = client.get("/riego")
        assert 'id="irrigation-schedule"' in resp.text

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/riego")
        html = resp.text
        assert "Seleccione una granja" in html
        assert "Seleccione un campo" in html

    def test_page_has_js_script(self, client):
        resp = client.get("/riego")
        assert "irrigation.js" in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/riego")
        assert "intel-nav" in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/riego")
        html = resp.text
        assert 'id="irrigation-total-liters"' in html
        assert 'id="irrigation-urgency"' in html


class TestIrrigationAPI:
    """Irrigation API returns expected data for seeded fields."""

    def test_irrigation_returns_200(self, client, db):
        farm, field = _seed_irrigation_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/irrigation")
        assert resp.status_code == 200

    def test_irrigation_has_schedule(self, client, db):
        farm, field = _seed_irrigation_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/irrigation")
        data = resp.json()
        assert "schedule" in data
        assert len(data["schedule"]) > 0

    def test_irrigation_has_urgency(self, client, db):
        farm, field = _seed_irrigation_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/irrigation")
        data = resp.json()
        assert "urgencia" in data
        assert data["urgencia"] in ("alta", "media", "baja")

    def test_irrigation_has_total_liters(self, client, db):
        farm, field = _seed_irrigation_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/irrigation")
        data = resp.json()
        assert "liters_total_per_ha" in data
        assert data["liters_total_per_ha"] > 0

    def test_irrigation_has_recommendation(self, client, db):
        farm, field = _seed_irrigation_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/irrigation")
        data = resp.json()
        assert "recomendacion" in data
        assert len(data["recomendacion"]) > 0

    def test_irrigation_schedule_days(self, client, db):
        farm, field = _seed_irrigation_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/irrigation")
        data = resp.json()
        for entry in data["schedule"]:
            assert "day" in entry
            assert "liters_per_ha" in entry
            assert "nota" in entry

    def test_irrigation_empty_data(self, client, db):
        farm, field = _seed_empty_farm(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/irrigation")
        assert resp.status_code == 200
        data = resp.json()
        assert "schedule" in data

    def test_irrigation_404_missing_farm(self, client, db):
        resp = client.get("/api/farms/9999/fields/1/irrigation")
        assert resp.status_code == 404

    def test_irrigation_404_missing_field(self, client, db):
        farm, field = _seed_irrigation_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/9999/irrigation")
        assert resp.status_code == 404


class TestIrrigationPageContent:
    """Page HTML has correct structure for irrigation rendering."""

    def test_page_has_riego_link_in_nav(self, client):
        resp = client.get("/riego")
        assert "/riego" in resp.text

    def test_page_has_content_container(self, client):
        resp = client.get("/riego")
        assert 'id="irrigation-content"' in resp.text

    def test_page_has_schedule_table_header(self, client):
        resp = client.get("/riego")
        html = resp.text
        assert "Dia" in html or "dia" in html

    def test_page_has_urgency_display(self, client):
        resp = client.get("/riego")
        assert 'id="irrigation-urgency"' in resp.text

    def test_page_has_recommendation_section(self, client):
        resp = client.get("/riego")
        assert 'id="irrigation-recommendation"' in resp.text
