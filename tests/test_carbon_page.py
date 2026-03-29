"""Tests for the soil carbon sequestration report page at /carbono."""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Farm, Field, SoilAnalysis
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


def _seed_carbon_data(db):
    """Seed farm, fields, and soil analyses with organic matter for carbon reports."""
    farm = Farm(name="Rancho Carbono", state="Jalisco", total_hectares=50.0)
    db.add(farm)
    db.flush()
    f1 = Field(farm_id=farm.id, name="Parcela Norte", hectares=20.0, crop_type="maiz")
    f2 = Field(farm_id=farm.id, name="Parcela Sur", hectares=15.0, crop_type="aguacate")
    db.add_all([f1, f2])
    db.flush()

    # Soil analyses with organic matter data — field 1 improving
    db.add_all([
        SoilAnalysis(
            field_id=f1.id, ph=6.2, organic_matter_pct=2.0,
            nitrogen_ppm=35.0, phosphorus_ppm=18.0, potassium_ppm=160.0,
            texture="franco", moisture_pct=22.0, sampled_at=datetime(2025, 6, 1),
        ),
        SoilAnalysis(
            field_id=f1.id, ph=6.4, organic_matter_pct=2.8,
            nitrogen_ppm=42.0, phosphorus_ppm=22.0, potassium_ppm=175.0,
            texture="franco", moisture_pct=28.0, sampled_at=datetime(2025, 12, 1),
        ),
        SoilAnalysis(
            field_id=f1.id, ph=6.5, organic_matter_pct=3.2,
            nitrogen_ppm=48.0, phosphorus_ppm=26.0, potassium_ppm=185.0,
            texture="franco", moisture_pct=30.0, sampled_at=datetime(2026, 3, 1),
        ),
    ])

    # Soil analyses for field 2
    db.add_all([
        SoilAnalysis(
            field_id=f2.id, ph=5.8, organic_matter_pct=3.5,
            nitrogen_ppm=50.0, phosphorus_ppm=28.0, potassium_ppm=190.0,
            texture="arcilloso", moisture_pct=35.0, sampled_at=datetime(2025, 9, 1),
        ),
        SoilAnalysis(
            field_id=f2.id, ph=5.9, organic_matter_pct=3.8,
            nitrogen_ppm=55.0, phosphorus_ppm=30.0, potassium_ppm=200.0,
            texture="arcilloso", moisture_pct=33.0, sampled_at=datetime(2026, 2, 1),
        ),
    ])
    db.commit()
    return farm, f1, f2


class TestCarbonPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/carbono")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/carbono")
        assert "Carbono" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/carbono")
        assert 'id="carbon-farm-select"' in resp.text

    def test_page_has_field_selector(self, client):
        resp = client.get("/carbono")
        assert 'id="carbon-field-select"' in resp.text

    def test_page_has_chart_container(self, client):
        resp = client.get("/carbono")
        assert 'id="carbon-chart"' in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/carbono")
        html = resp.text
        assert 'id="carbon-soc-value"' in html
        assert 'id="carbon-co2e-value"' in html
        assert 'id="carbon-trend-value"' in html

    def test_page_has_empty_state(self, client):
        resp = client.get("/carbono")
        assert 'id="carbon-empty"' in resp.text

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/carbono")
        html = resp.text
        assert "Seleccione una granja" in html
        assert "Seleccione un campo" in html

    def test_page_has_js_script(self, client):
        resp = client.get("/carbono")
        assert "carbon.js" in resp.text

    def test_page_has_breakdown_table(self, client):
        resp = client.get("/carbono")
        assert 'id="carbon-fields-table"' in resp.text

    def test_page_has_summary_section(self, client):
        resp = client.get("/carbono")
        assert 'id="carbon-summary"' in resp.text


class TestCarbonFieldAPI:
    """Field-level carbon API returns expected data."""

    def test_field_carbon_returns_data(self, client, db):
        farm, f1, f2 = _seed_carbon_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{f1.id}/carbon")
        assert resp.status_code == 200
        data = resp.json()
        assert "field_id" in data
        assert "soc_actual" in data
        assert "tendencia" in data
        assert "resumen" in data

    def test_field_carbon_has_soc_data(self, client, db):
        farm, f1, f2 = _seed_carbon_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{f1.id}/carbon")
        data = resp.json()
        soc = data["soc_actual"]
        assert soc is not None
        assert "soc_tonnes_per_ha" in soc
        assert "clasificacion" in soc
        assert soc["soc_tonnes_per_ha"] > 0

    def test_improving_field_shows_gaining_trend(self, client, db):
        farm, f1, f2 = _seed_carbon_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{f1.id}/carbon")
        data = resp.json()
        # Field 1 has organic matter improving 2.0 → 2.8 → 3.2
        assert data["tendencia"] == "ganando"

    def test_empty_field_returns_insufficient_data(self, client, db):
        farm = Farm(name="Rancho Vacio", state="Jalisco", total_hectares=10.0)
        db.add(farm)
        db.flush()
        field = Field(farm_id=farm.id, name="Campo Nuevo", hectares=5.0, crop_type="frijol")
        db.add(field)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/carbon")
        data = resp.json()
        assert data["tendencia"] == "datos_insuficientes"
        assert data["soc_actual"] is None


class TestCarbonFarmAPI:
    """Farm-level carbon aggregate API returns expected data."""

    def test_farm_carbon_returns_summary(self, client, db):
        farm, f1, f2 = _seed_carbon_data(db)
        resp = client.get(f"/api/farms/{farm.id}/carbon")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_fields" in data
        assert "total_co2e_tonnes" in data
        assert "fields" in data

    def test_farm_carbon_includes_both_fields(self, client, db):
        farm, f1, f2 = _seed_carbon_data(db)
        resp = client.get(f"/api/farms/{farm.id}/carbon")
        data = resp.json()
        assert data["total_fields"] >= 2
        assert len(data["fields"]) >= 2

    def test_farm_carbon_has_co2e(self, client, db):
        farm, f1, f2 = _seed_carbon_data(db)
        resp = client.get(f"/api/farms/{farm.id}/carbon")
        data = resp.json()
        assert data["total_co2e_tonnes"] > 0

    def test_farm_carbon_404_for_missing_farm(self, client, db):
        resp = client.get("/api/farms/9999/carbon")
        assert resp.status_code == 404


class TestCarbonPageContent:
    """Page HTML has correct structure for carbon report rendering."""

    def test_page_has_nav(self, client):
        resp = client.get("/carbono")
        assert "intel-nav" in resp.text

    def test_page_has_chart_canvas(self, client):
        resp = client.get("/carbono")
        assert '<canvas id="carbon-chart"' in resp.text

    def test_page_has_co2e_explanation(self, client):
        resp = client.get("/carbono")
        assert "CO2" in resp.text or "co2" in resp.text.lower()

    def test_page_has_carbono_link_in_nav(self, client):
        resp = client.get("/carbono")
        assert "/carbono" in resp.text
