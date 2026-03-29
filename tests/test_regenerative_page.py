"""Tests for the regenerative scorecard page at /regenerativo."""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Farm, Field, TreatmentRecord, SoilAnalysis, MicrobiomeRecord
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


def _seed_regenerative_data(db):
    """Seed farm, field, treatments, soil analyses, and microbiome for scorecard."""
    farm = Farm(name="Rancho Regenerativo", state="Jalisco", total_hectares=30.0)
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Parcela Milpa", hectares=10.0, crop_type="maiz")
    db.add(field)
    db.flush()

    # Organic treatments with ancestral methods
    base = dict(
        field_id=field.id, health_score_used=65.0, problema="Suelo degradado",
        causa_probable="Falta de materia organica", urgencia="media",
        prevencion="Rotacion de cultivos", costo_estimado_mxn=500, organic=True,
    )
    t1 = TreatmentRecord(
        **base, tratamiento="Composta enriquecida",
        ancestral_method_name="Milpa", created_at=datetime(2026, 1, 15),
    )
    t2 = TreatmentRecord(
        **base, tratamiento="Extracto de neem",
        ancestral_method_name=None, created_at=datetime(2026, 2, 10),
    )
    t3 = TreatmentRecord(
        **base, tratamiento="Ceniza volcanica",
        ancestral_method_name="Ceniza volcánica", created_at=datetime(2026, 3, 5),
    )
    db.add_all([t1, t2, t3])

    # Soil analyses showing improvement
    s1 = SoilAnalysis(
        field_id=field.id, ph=6.0, organic_matter_pct=2.5,
        nitrogen_ppm=40.0, phosphorus_ppm=20.0, potassium_ppm=170.0,
        texture="franco", moisture_pct=25.0,
        sampled_at=datetime(2026, 1, 5),
    )
    s2 = SoilAnalysis(
        field_id=field.id, ph=6.3, organic_matter_pct=3.5,
        nitrogen_ppm=50.0, phosphorus_ppm=25.0, potassium_ppm=190.0,
        texture="franco", moisture_pct=30.0,
        sampled_at=datetime(2026, 3, 5),
    )
    db.add_all([s1, s2])

    # Healthy microbiome
    micro = MicrobiomeRecord(
        field_id=field.id, classification="healthy",
        fungi_bacteria_ratio=0.8, respiration_rate=12.0,
        microbial_biomass_carbon=250.0,
        sampled_at=datetime(2026, 2, 20),
    )
    db.add(micro)
    db.commit()
    return farm, field


class TestRegenerativePageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/regenerativo")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/regenerativo")
        assert "Regenerativo" in resp.text or "Scorecard" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/regenerativo")
        assert 'id="regen-farm-select"' in resp.text

    def test_page_has_field_selector(self, client):
        resp = client.get("/regenerativo")
        assert 'id="regen-field-select"' in resp.text

    def test_page_has_score_gauge(self, client):
        resp = client.get("/regenerativo")
        assert 'id="regen-score-value"' in resp.text

    def test_page_has_breakdown_cards(self, client):
        resp = client.get("/regenerativo")
        html = resp.text
        assert 'id="regen-organic"' in html
        assert 'id="regen-ancestral"' in html
        assert 'id="regen-soil"' in html
        assert 'id="regen-microbiome"' in html
        assert 'id="regen-diversity"' in html

    def test_page_has_recommendations_container(self, client):
        resp = client.get("/regenerativo")
        assert 'id="regen-recommendations"' in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/regenerativo")
        html = resp.text
        assert 'id="regen-total-score"' in html
        assert 'id="regen-treatments-count"' in html

    def test_page_has_empty_state(self, client):
        resp = client.get("/regenerativo")
        assert 'id="regen-empty"' in resp.text

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/regenerativo")
        html = resp.text
        assert "Seleccione una granja" in html
        assert "Seleccione un campo" in html

    def test_page_has_js_script(self, client):
        resp = client.get("/regenerativo")
        assert "regenerative.js" in resp.text

    def test_page_has_breakdown_labels_in_spanish(self, client):
        resp = client.get("/regenerativo")
        html = resp.text
        assert "Tratamientos" in html  # Organic treatments
        assert "Ancestral" in html or "ancestral" in html
        assert "Suelo" in html or "suelo" in html
        assert "Microbioma" in html or "microbioma" in html
        assert "Diversidad" in html or "diversidad" in html


class TestRegenerativeAPI:
    """Regenerative score API returns expected data."""

    def test_score_endpoint_returns_data(self, client, db):
        farm, field = _seed_regenerative_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/regenerative-score")
        assert resp.status_code == 200
        data = resp.json()
        assert "score" in data
        assert "breakdown" in data
        assert "recommendations" in data

    def test_score_is_between_0_and_100(self, client, db):
        farm, field = _seed_regenerative_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/regenerative-score")
        data = resp.json()
        assert 0 <= data["score"] <= 100

    def test_breakdown_has_all_components(self, client, db):
        farm, field = _seed_regenerative_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/regenerative-score")
        breakdown = resp.json()["breakdown"]
        assert "organic_treatments" in breakdown
        assert "ancestral_methods" in breakdown
        assert "soil_organic_trend" in breakdown
        assert "microbiome_health" in breakdown
        assert "treatment_diversity" in breakdown

    def test_score_with_good_data_is_high(self, client, db):
        farm, field = _seed_regenerative_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/regenerative-score")
        data = resp.json()
        # All organic treatments, ancestral methods, improving soil, healthy microbiome
        assert data["score"] >= 60

    def test_empty_field_returns_zero(self, client, db):
        farm = Farm(name="Rancho Vacio", state="Jalisco", total_hectares=10.0)
        db.add(farm)
        db.flush()
        field = Field(farm_id=farm.id, name="Campo Vacio", hectares=5.0, crop_type="frijol")
        db.add(field)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/regenerative-score")
        data = resp.json()
        assert data["score"] == 0


class TestRegenerativePageContent:
    """Page HTML has correct structure for scorecard rendering."""

    def test_page_has_gauge_container(self, client):
        resp = client.get("/regenerativo")
        assert 'id="regen-gauge"' in resp.text

    def test_page_has_nav_link(self, client):
        resp = client.get("/regenerativo")
        assert "/regenerativo" in resp.text
