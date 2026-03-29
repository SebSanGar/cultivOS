"""Tests for the sensor fusion validation page at /fusion."""

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Farm, Field, NDVIResult, ThermalResult, SoilAnalysis
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


def _seed_fusion_data(db):
    """Seed farm, field, NDVI, thermal, and soil for fusion analysis."""
    farm = Farm(name="Rancho Fusion", state="Jalisco", total_hectares=80.0)
    db.add(farm)
    db.flush()
    field = Field(
        farm_id=farm.id, name="Parcela Sensores", hectares=25.0, crop_type="maiz",
    )
    db.add(field)
    db.flush()
    ndvi = NDVIResult(
        field_id=field.id, ndvi_mean=0.72, ndvi_std=0.08, ndvi_min=0.5, ndvi_max=0.9,
        pixels_total=50000, stress_pct=10.0,
        zones=[{"zone": "centro", "mean": 0.7}],
    )
    thermal = ThermalResult(
        field_id=field.id, stress_pct=38.0, irrigation_deficit=True,
        temp_mean=36.0, temp_std=3.5, temp_min=28.0, temp_max=42.0,
        pixels_total=50000, analyzed_at=datetime(2026, 3, 15),
    )
    soil = SoilAnalysis(
        field_id=field.id, ph=6.2, organic_matter_pct=3.5,
        nitrogen_ppm=30.0, phosphorus_ppm=18.0, potassium_ppm=120.0,
        moisture_pct=28.0, sampled_at=datetime(2026, 3, 10),
    )
    db.add_all([ndvi, thermal, soil])
    db.commit()
    return farm, field


def _seed_empty_farm(db):
    """Seed farm with field but no sensor data."""
    farm = Farm(name="Rancho Vacio", state="Jalisco", total_hectares=15.0)
    db.add(farm)
    db.flush()
    field = Field(
        farm_id=farm.id, name="Parcela Sin Sensores", hectares=5.0, crop_type="frijol",
    )
    db.add(field)
    db.commit()
    return farm, field


class TestFusionPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/fusion")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/fusion")
        assert "Fusion" in resp.text or "Sensores" in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/fusion")
        assert "intel-nav" in resp.text

    def test_page_has_empty_state(self, client):
        resp = client.get("/fusion")
        assert 'id="fusion-empty"' in resp.text

    def test_page_has_matrix_container(self, client):
        resp = client.get("/fusion")
        assert 'id="fusion-matrix"' in resp.text

    def test_page_has_contradictions_container(self, client):
        resp = client.get("/fusion")
        assert 'id="fusion-contradictions"' in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/fusion")
        html = resp.text
        assert 'id="fusion-total-fields"' in html
        assert 'id="fusion-avg-confidence"' in html
        assert 'id="fusion-total-contradictions"' in html

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/fusion")
        html = resp.text
        assert "Confianza" in html
        assert "Contradicciones" in html

    def test_page_has_js_script(self, client):
        resp = client.get("/fusion")
        assert "fusion-page.js" in resp.text

    def test_page_has_load_button(self, client):
        resp = client.get("/fusion")
        assert "Analizar" in resp.text or "Consultar" in resp.text


class TestFusionAPI:
    """Sensor fusion overview API returns expected data."""

    def test_fusion_overview_returns_200(self, client, db):
        _seed_fusion_data(db)
        resp = client.get("/api/intel/sensor-fusion")
        assert resp.status_code == 200

    def test_fusion_overview_has_fields(self, client, db):
        _seed_fusion_data(db)
        resp = client.get("/api/intel/sensor-fusion")
        data = resp.json()
        assert "fields" in data
        assert isinstance(data["fields"], list)
        assert len(data["fields"]) > 0

    def test_fusion_field_has_confidence(self, client, db):
        _seed_fusion_data(db)
        resp = client.get("/api/intel/sensor-fusion")
        data = resp.json()
        entry = data["fields"][0]
        assert "confidence" in entry
        assert 0 <= entry["confidence"] <= 1

    def test_fusion_field_has_sensors_used(self, client, db):
        _seed_fusion_data(db)
        resp = client.get("/api/intel/sensor-fusion")
        data = resp.json()
        entry = data["fields"][0]
        assert "sensors_used" in entry
        assert len(entry["sensors_used"]) > 0

    def test_fusion_field_has_contradictions(self, client, db):
        _seed_fusion_data(db)
        resp = client.get("/api/intel/sensor-fusion")
        data = resp.json()
        entry = data["fields"][0]
        assert "contradictions" in entry
        assert isinstance(entry["contradictions"], list)

    def test_fusion_field_has_assessment(self, client, db):
        _seed_fusion_data(db)
        resp = client.get("/api/intel/sensor-fusion")
        data = resp.json()
        entry = data["fields"][0]
        assert "assessment" in entry
        assert len(entry["assessment"]) > 0

    def test_fusion_overview_totals(self, client, db):
        _seed_fusion_data(db)
        resp = client.get("/api/intel/sensor-fusion")
        data = resp.json()
        assert "total_fields" in data
        assert "fields_with_data" in data
        assert "avg_confidence" in data
        assert "total_contradictions" in data
        assert data["fields_with_data"] >= 1

    def test_fusion_detects_ndvi_thermal_contradiction(self, client, db):
        """NDVI healthy (0.72) but thermal stressed (38%) should flag contradiction."""
        _seed_fusion_data(db)
        resp = client.get("/api/intel/sensor-fusion")
        data = resp.json()
        entry = data["fields"][0]
        # Seeded: NDVI healthy (0.72, 10% stress) + thermal stressed (38%, 36C)
        assert len(entry["contradictions"]) > 0
        tags = [c["tag"] for c in entry["contradictions"]]
        assert "ndvi_thermal_mismatch" in tags

    def test_fusion_empty_fields_excluded(self, client, db):
        _seed_empty_farm(db)
        resp = client.get("/api/intel/sensor-fusion")
        data = resp.json()
        assert data["fields_with_data"] == 0
        assert len(data["fields"]) == 0


class TestFusionPageContent:
    """Page HTML has correct structure for fusion rendering."""

    def test_page_has_field_cards_container(self, client):
        resp = client.get("/fusion")
        assert 'id="fusion-field-cards"' in resp.text

    def test_page_has_confidence_label(self, client):
        resp = client.get("/fusion")
        assert "Confianza Promedio" in resp.text or "Confianza" in resp.text

    def test_page_has_sensors_label(self, client):
        resp = client.get("/fusion")
        assert "Sensores" in resp.text

    def test_page_has_fusion_link_in_nav(self, client):
        resp = client.get("/fusion")
        assert "/fusion" in resp.text
