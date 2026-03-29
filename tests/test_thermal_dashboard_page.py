"""Tests for the thermal stress dashboard page at /termica."""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Farm, Field, ThermalResult
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


def _seed_thermal_data(db):
    """Seed a farm with fields and thermal analysis results."""
    farm = Farm(name="Rancho Termica", state="Jalisco", total_hectares=30.0)
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Parcela Agave", hectares=10.0, crop_type="agave")
    db.add(field)
    db.flush()
    t1 = ThermalResult(
        field_id=field.id, flight_id=None,
        temp_mean=28.5, temp_std=2.1, temp_min=24.0, temp_max=35.0,
        pixels_total=50000, stress_pct=12.3, irrigation_deficit=False,
        analyzed_at=datetime(2026, 1, 15),
    )
    t2 = ThermalResult(
        field_id=field.id, flight_id=None,
        temp_mean=32.0, temp_std=3.5, temp_min=26.0, temp_max=41.0,
        pixels_total=50000, stress_pct=28.7, irrigation_deficit=True,
        analyzed_at=datetime(2026, 2, 15),
    )
    t3 = ThermalResult(
        field_id=field.id, flight_id=None,
        temp_mean=30.2, temp_std=2.8, temp_min=25.0, temp_max=38.0,
        pixels_total=50000, stress_pct=19.5, irrigation_deficit=False,
        analyzed_at=datetime(2026, 3, 15),
    )
    db.add_all([t1, t2, t3])
    db.commit()
    return farm, field


class TestThermalPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/termica")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/termica")
        assert "Termica" in resp.text or "rmica" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/termica")
        assert 'id="thermal-farm-select"' in resp.text

    def test_page_has_field_selector(self, client):
        resp = client.get("/termica")
        assert 'id="thermal-field-select"' in resp.text

    def test_page_has_chart_containers(self, client):
        resp = client.get("/termica")
        html = resp.text
        assert 'id="thermal-stress-chart"' in html
        assert 'id="thermal-temp-chart"' in html

    def test_page_has_stats_strip(self, client):
        resp = client.get("/termica")
        html = resp.text
        assert 'id="thermal-analysis-count"' in html
        assert 'id="thermal-latest-stress"' in html
        assert 'id="thermal-latest-temp"' in html
        assert 'id="thermal-deficit-count"' in html

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/termica")
        html = resp.text
        assert "Seleccione una granja" in html
        assert "Seleccione un campo" in html

    def test_page_has_empty_state(self, client):
        resp = client.get("/termica")
        assert 'id="thermal-empty"' in resp.text

    def test_page_has_js_script(self, client):
        resp = client.get("/termica")
        assert "thermal-dashboard.js" in resp.text

    def test_page_has_chartjs(self, client):
        resp = client.get("/termica")
        assert "chart.js" in resp.text.lower() or "Chart" in resp.text


class TestThermalAPIs:
    """Thermal list API returns expected data."""

    def test_thermal_list_returns_results(self, client, db):
        farm, field = _seed_thermal_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/thermal")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3

    def test_thermal_list_has_expected_fields(self, client, db):
        farm, field = _seed_thermal_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/thermal")
        data = resp.json()
        entry = data[0]
        assert "temp_mean" in entry
        assert "stress_pct" in entry
        assert "irrigation_deficit" in entry
        assert "analyzed_at" in entry

    def test_thermal_list_empty_field(self, client, db):
        farm = Farm(name="Rancho Vacio", state="Jalisco", total_hectares=10.0)
        db.add(farm)
        db.flush()
        field = Field(farm_id=farm.id, name="Campo Sin Datos", hectares=5.0, crop_type="maiz")
        db.add(field)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/thermal")
        assert resp.status_code == 200
        assert resp.json() == []


class TestThermalPageContent:
    """Page HTML has correct structure for thermal dashboard."""

    def test_page_has_data_table(self, client):
        resp = client.get("/termica")
        assert 'id="thermal-table"' in resp.text

    def test_page_has_chart_section_labels(self, client):
        resp = client.get("/termica")
        html = resp.text
        assert "Estr" in html  # "Estres Termico" or "Estres"
        assert "Temperatura" in html

    def test_page_has_irrigation_deficit_indicator(self, client):
        resp = client.get("/termica")
        assert "ficit" in resp.text  # "Deficit de Riego"

    def test_page_has_stylesheet(self, client):
        resp = client.get("/termica")
        assert "styles.css" in resp.text
