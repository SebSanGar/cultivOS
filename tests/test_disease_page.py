"""Tests for the disease risk assessment page at /enfermedades."""

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Disease, Farm, Field, NDVIResult, ThermalResult, WeatherRecord
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


def _seed_disease_data(db):
    """Seed farm, field, NDVI, thermal, weather, and disease records."""
    farm = Farm(name="Rancho Enfermo", state="Jalisco", total_hectares=60.0)
    db.add(farm)
    db.flush()
    field = Field(
        farm_id=farm.id, name="Parcela Riesgo", hectares=20.0, crop_type="maiz",
    )
    db.add(field)
    db.flush()
    ndvi = NDVIResult(
        field_id=field.id, ndvi_mean=0.35, ndvi_std=0.18, ndvi_min=0.1, ndvi_max=0.6,
        pixels_total=40000, stress_pct=42.0,
        zones=[{"zone": "norte", "mean": 0.3}],
    )
    thermal = ThermalResult(
        field_id=field.id, stress_pct=30.0, irrigation_deficit=True,
        temp_mean=30.5, temp_std=4.0, temp_min=24.0, temp_max=40.0,
        pixels_total=40000, analyzed_at=datetime(2026, 3, 1),
    )
    weather = WeatherRecord(
        farm_id=farm.id, temp_c=31.0, humidity_pct=75.0, rainfall_mm=15.0,
        wind_kmh=8.0, description="Lluvioso", forecast_3day=[],
        recorded_at=datetime(2026, 3, 1),
    )
    disease = Disease(
        name="Roya del maiz",
        description_es="Enfermedad fungica que causa pustulas anaranjadas en hojas",
        symptoms=["pustulas anaranjadas", "hojas amarillas", "defoliacion"],
        affected_crops=["maiz", "sorgo"],
        treatments=[
            {"name": "Extracto de neem", "description_es": "Aplicar foliarmente cada 7 dias", "organic": True},
        ],
        region="Jalisco",
        severity="alta",
    )
    db.add_all([ndvi, thermal, weather, disease])
    db.commit()
    return farm, field


def _seed_empty_farm(db):
    """Seed farm with field but no NDVI/thermal/weather data."""
    farm = Farm(name="Rancho Limpio", state="Jalisco", total_hectares=25.0)
    db.add(farm)
    db.flush()
    field = Field(
        farm_id=farm.id, name="Parcela Sin Datos", hectares=8.0, crop_type="frijol",
    )
    db.add(field)
    db.commit()
    return farm, field


class TestDiseasePageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/enfermedades")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/enfermedades")
        assert "Enfermedades" in resp.text or "Riesgo" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/enfermedades")
        assert 'id="disease-farm-select"' in resp.text

    def test_page_has_field_selector(self, client):
        resp = client.get("/enfermedades")
        assert 'id="disease-field-select"' in resp.text

    def test_page_has_load_button(self, client):
        resp = client.get("/enfermedades")
        assert "Consultar" in resp.text

    def test_page_has_empty_state(self, client):
        resp = client.get("/enfermedades")
        assert 'id="disease-empty"' in resp.text

    def test_page_has_risk_container(self, client):
        resp = client.get("/enfermedades")
        assert 'id="disease-risk-content"' in resp.text

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/enfermedades")
        html = resp.text
        assert "Seleccione una granja" in html
        assert "Seleccione un campo" in html

    def test_page_has_js_script(self, client):
        resp = client.get("/enfermedades")
        assert "disease.js" in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/enfermedades")
        assert "intel-nav" in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/enfermedades")
        html = resp.text
        assert 'id="disease-risk-level"' in html
        assert 'id="disease-risk-count"' in html


class TestDiseaseRiskAPI:
    """Disease risk API returns expected data for seeded fields."""

    def test_disease_risk_returns_200(self, client, db):
        farm, field = _seed_disease_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/disease-risk")
        assert resp.status_code == 200

    def test_disease_risk_has_level(self, client, db):
        farm, field = _seed_disease_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/disease-risk")
        data = resp.json()
        assert "risk_level" in data
        assert data["risk_level"] in ("alto", "medio", "bajo", "sin_riesgo")

    def test_disease_risk_has_risks_list(self, client, db):
        farm, field = _seed_disease_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/disease-risk")
        data = resp.json()
        assert "risks" in data
        assert isinstance(data["risks"], list)

    def test_disease_risk_items_have_fields(self, client, db):
        farm, field = _seed_disease_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/disease-risk")
        data = resp.json()
        if data["risks"]:
            risk = data["risks"][0]
            assert "tipo" in risk
            assert "descripcion" in risk
            assert "recomendacion" in risk
            assert "urgencia" in risk

    def test_disease_risk_has_mensaje(self, client, db):
        farm, field = _seed_disease_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/disease-risk")
        data = resp.json()
        assert "mensaje" in data
        assert len(data["mensaje"]) > 0

    def test_disease_risk_empty_data(self, client, db):
        farm, field = _seed_empty_farm(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/disease-risk")
        assert resp.status_code == 200
        data = resp.json()
        assert data["risk_level"] == "sin_riesgo"

    def test_disease_risk_404_missing_farm(self, client, db):
        resp = client.get("/api/farms/9999/fields/1/disease-risk")
        assert resp.status_code == 404

    def test_disease_risk_404_missing_field(self, client, db):
        farm, field = _seed_disease_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/9999/disease-risk")
        assert resp.status_code == 404


class TestDiseaseIdentifyAPI:
    """Disease identification endpoint returns ranked matches."""

    def test_identify_returns_200(self, client, db):
        _seed_disease_data(db)
        resp = client.post("/api/knowledge/diseases/identify", json={
            "symptoms": ["pustulas anaranjadas", "hojas amarillas"],
            "crop": "maiz",
        })
        assert resp.status_code == 200

    def test_identify_returns_matches(self, client, db):
        _seed_disease_data(db)
        resp = client.post("/api/knowledge/diseases/identify", json={
            "symptoms": ["pustulas anaranjadas"],
        })
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_identify_match_has_confidence(self, client, db):
        _seed_disease_data(db)
        resp = client.post("/api/knowledge/diseases/identify", json={
            "symptoms": ["pustulas anaranjadas"],
        })
        data = resp.json()
        assert data[0]["confidence"] > 0

    def test_identify_match_has_name(self, client, db):
        _seed_disease_data(db)
        resp = client.post("/api/knowledge/diseases/identify", json={
            "symptoms": ["pustulas anaranjadas"],
        })
        data = resp.json()
        assert "name" in data[0]
        assert "Roya" in data[0]["name"]

    def test_identify_match_has_treatments(self, client, db):
        _seed_disease_data(db)
        resp = client.post("/api/knowledge/diseases/identify", json={
            "symptoms": ["pustulas anaranjadas"],
        })
        data = resp.json()
        assert "treatments" in data[0]
        assert len(data[0]["treatments"]) > 0


class TestDiseasePageContent:
    """Page HTML has correct structure for disease risk rendering."""

    def test_page_has_identify_form(self, client):
        resp = client.get("/enfermedades")
        assert 'id="disease-identify-form"' in resp.text

    def test_page_has_symptoms_input(self, client):
        resp = client.get("/enfermedades")
        assert 'id="disease-symptoms-input"' in resp.text

    def test_page_has_identify_button(self, client):
        resp = client.get("/enfermedades")
        assert "Identificar" in resp.text

    def test_page_has_identify_results(self, client):
        resp = client.get("/enfermedades")
        assert 'id="disease-identify-results"' in resp.text

    def test_page_has_risk_cards_container(self, client):
        resp = client.get("/enfermedades")
        assert 'id="disease-risk-cards"' in resp.text

    def test_page_has_enfermedades_link_in_nav(self, client):
        resp = client.get("/enfermedades")
        assert "/enfermedades" in resp.text
