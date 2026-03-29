"""Tests for TEK ancestral knowledge validation page at /tek."""

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Farm, Field, TreatmentRecord, FarmerFeedback
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


def _seed_tek_data(db):
    """Seed farm, field, treatments with ancestral methods, and farmer feedback."""
    farm = Farm(name="Rancho TEK", state="Jalisco", total_hectares=50.0)
    db.add(farm)
    db.flush()
    field = Field(
        farm_id=farm.id, name="Parcela Ancestral", hectares=10.0, crop_type="maiz",
    )
    db.add(field)
    db.flush()
    # Treatment with ancestral method
    t1 = TreatmentRecord(
        field_id=field.id,
        treatment_type="organic",
        description="Caldo bordeles para hongos",
        ancestral_method_name="Caldo Bordeles",
        applied_at=datetime(2026, 3, 1),
    )
    t2 = TreatmentRecord(
        field_id=field.id,
        treatment_type="organic",
        description="Composta de lombriz",
        ancestral_method_name="Lombricomposta",
        applied_at=datetime(2026, 3, 5),
    )
    db.add_all([t1, t2])
    db.flush()
    # Feedback for treatments
    fb1 = FarmerFeedback(
        field_id=field.id, treatment_id=t1.id,
        rating=5, worked=True, farmer_notes="Funciono muy bien",
    )
    fb2 = FarmerFeedback(
        field_id=field.id, treatment_id=t1.id,
        rating=4, worked=True, farmer_notes="Buen resultado",
    )
    fb3 = FarmerFeedback(
        field_id=field.id, treatment_id=t2.id,
        rating=3, worked=False, farmer_notes="No vi cambio",
    )
    db.add_all([fb1, fb2, fb3])
    db.commit()
    return farm, field


class TestTEKPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/tek")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/tek")
        assert "Validacion" in resp.text and "TEK" in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/tek")
        assert "intel-nav" in resp.text

    def test_page_has_empty_state(self, client):
        resp = client.get("/tek")
        assert 'id="tek-empty"' in resp.text

    def test_page_has_methods_container(self, client):
        resp = client.get("/tek")
        assert 'id="tek-methods"' in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/tek")
        html = resp.text
        assert 'id="tek-total-methods"' in html
        assert 'id="tek-avg-trust"' in html
        assert 'id="tek-total-feedback"' in html

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/tek")
        html = resp.text
        assert "Confianza" in html
        assert "Metodos" in html

    def test_page_has_js_script(self, client):
        resp = client.get("/tek")
        assert "tek-page.js" in resp.text

    def test_page_has_load_button(self, client):
        resp = client.get("/tek")
        assert "Consultar" in resp.text or "Cargar" in resp.text


class TestTEKPageJS:
    """JavaScript file contains required functions and elements."""

    def test_js_returns_200(self, client):
        resp = client.get("/tek-page.js")
        assert resp.status_code == 200

    def test_js_has_load_function(self, client):
        resp = client.get("/tek-page.js")
        assert "loadTEKData" in resp.text

    def test_js_calls_tek_validation_api(self, client):
        resp = client.get("/tek-page.js")
        assert "/api/intel/tek-validation" in resp.text

    def test_js_renders_trust_score(self, client):
        resp = client.get("/tek-page.js")
        js = resp.text
        assert "trust_score" in js

    def test_js_renders_method_name(self, client):
        resp = client.get("/tek-page.js")
        assert "method_name" in js if (js := resp.text) else False

    def test_js_renders_feedback_counts(self, client):
        resp = client.get("/tek-page.js")
        js = resp.text
        assert "positive_count" in js
        assert "negative_count" in js

    def test_js_has_empty_state_message(self, client):
        resp = client.get("/tek-page.js")
        assert "Sin datos" in resp.text or "sin metodos" in resp.text.lower()

    def test_js_has_method_card_class(self, client):
        resp = client.get("/tek-page.js")
        assert "tek-method-card" in resp.text

    def test_js_has_filter_by_type(self, client):
        resp = client.get("/tek-page.js")
        assert "filterMethods" in resp.text or "filter" in resp.text.lower()


class TestTEKPageContent:
    """Page HTML has correct structure."""

    def test_page_has_filter_dropdown(self, client):
        resp = client.get("/tek")
        assert 'id="tek-filter"' in resp.text

    def test_page_has_tek_link_in_nav(self, client):
        resp = client.get("/tek")
        assert "/tek" in resp.text

    def test_page_has_subtitle(self, client):
        resp = client.get("/tek")
        assert "ancestral" in resp.text.lower() or "tradicional" in resp.text.lower()
