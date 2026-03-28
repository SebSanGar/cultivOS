"""Tests for the soil analysis history page at /suelo."""

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


def _seed_soil_data(db):
    """Seed a farm with fields and soil analyses over time."""
    farm = Farm(name="Rancho Suelo", state="Jalisco", total_hectares=20.0)
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Parcela Aguacate", hectares=8.0, crop_type="aguacate")
    db.add(field)
    db.flush()
    s1 = SoilAnalysis(
        field_id=field.id, ph=6.2, organic_matter_pct=3.1,
        nitrogen_ppm=45.0, phosphorus_ppm=22.0, potassium_ppm=180.0,
        texture="franco-arcilloso", moisture_pct=28.0,
        sampled_at=datetime(2026, 1, 10),
    )
    s2 = SoilAnalysis(
        field_id=field.id, ph=6.4, organic_matter_pct=3.5,
        nitrogen_ppm=50.0, phosphorus_ppm=25.0, potassium_ppm=190.0,
        texture="franco-arcilloso", moisture_pct=30.0,
        sampled_at=datetime(2026, 2, 10),
    )
    s3 = SoilAnalysis(
        field_id=field.id, ph=6.5, organic_matter_pct=3.8,
        nitrogen_ppm=55.0, phosphorus_ppm=28.0, potassium_ppm=200.0,
        texture="franco-arcilloso", moisture_pct=32.0,
        sampled_at=datetime(2026, 3, 10),
    )
    db.add_all([s1, s2, s3])
    db.commit()
    return farm, field


class TestSoilPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/suelo")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/suelo")
        assert "Suelo" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/suelo")
        assert 'id="soil-farm-select"' in resp.text

    def test_page_has_field_selector(self, client):
        resp = client.get("/suelo")
        assert 'id="soil-field-select"' in resp.text

    def test_page_has_chart_containers(self, client):
        resp = client.get("/suelo")
        html = resp.text
        assert 'id="soil-ph-chart"' in html
        assert 'id="soil-om-chart"' in html
        assert 'id="soil-npk-chart"' in html

    def test_page_has_stats_strip(self, client):
        resp = client.get("/suelo")
        html = resp.text
        assert 'id="soil-sample-count"' in html
        assert 'id="soil-latest-ph"' in html
        assert 'id="soil-latest-om"' in html

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/suelo")
        html = resp.text
        assert "Seleccione una granja" in html
        assert "Seleccione un campo" in html

    def test_page_has_empty_state(self, client):
        resp = client.get("/suelo")
        assert 'id="soil-empty"' in resp.text

    def test_page_has_js_script(self, client):
        resp = client.get("/suelo")
        assert "soil-history.js" in resp.text

    def test_page_has_chartjs(self, client):
        resp = client.get("/suelo")
        assert "chart.js" in resp.text.lower() or "Chart" in resp.text


class TestSoilAPIs:
    """Soil list and trends APIs return expected data."""

    def test_soil_list_returns_analyses(self, client, db):
        farm, field = _seed_soil_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/soil")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3

    def test_soil_list_has_expected_fields(self, client, db):
        farm, field = _seed_soil_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/soil")
        data = resp.json()
        entry = data[0]
        assert "ph" in entry
        assert "organic_matter_pct" in entry
        assert "nitrogen_ppm" in entry
        assert "phosphorus_ppm" in entry
        assert "potassium_ppm" in entry
        assert "sampled_at" in entry

    def test_soil_trends_returns_data(self, client, db):
        farm, field = _seed_soil_data(db)
        resp = client.get("/api/intel/soil-trends")
        assert resp.status_code == 200
        data = resp.json()
        assert "trends" in data
        assert len(data["trends"]) >= 1


class TestSoilPageContent:
    """Page HTML has correct structure for chart rendering."""

    def test_page_has_data_table_container(self, client):
        resp = client.get("/suelo")
        assert 'id="soil-table"' in resp.text

    def test_page_has_chart_section_labels(self, client):
        resp = client.get("/suelo")
        html = resp.text
        assert "pH" in html
        assert "Materia" in html  # "Materia Organica"
        assert "NPK" in html or "Nutrientes" in html
