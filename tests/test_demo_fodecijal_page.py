"""Tests for the guided FODECIJAL demo flow page at /demo-fodecijal."""

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
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


# -- Page Load Tests --


class TestDemoFodecijalPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/demo-fodecijal")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/demo-fodecijal")
        assert "FODECIJAL" in resp.text

    def test_page_has_body_class(self, client):
        resp = client.get("/demo-fodecijal")
        assert 'class="intel-body"' in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/demo-fodecijal")
        assert "intel-nav" in resp.text

    def test_page_has_progress_bar(self, client):
        resp = client.get("/demo-fodecijal")
        assert 'id="progress-bar"' in resp.text

    def test_page_has_progress_text(self, client):
        resp = client.get("/demo-fodecijal")
        assert 'id="progress-text"' in resp.text

    def test_page_has_steps_container(self, client):
        resp = client.get("/demo-fodecijal")
        assert 'id="demo-steps"' in resp.text


# -- Step Content Tests --


class TestDemoSteps:
    """All 8 demo steps are present with correct structure."""

    STEP_IDS = [
        "step-1",
        "step-2",
        "step-3",
        "step-4",
        "step-5",
        "step-6",
        "step-7",
        "step-8",
    ]

    def test_has_8_steps(self, client):
        resp = client.get("/demo-fodecijal")
        for step_id in self.STEP_IDS:
            assert f'id="{step_id}"' in resp.text

    def test_step_1_farm_map(self, client):
        resp = client.get("/demo-fodecijal")
        assert "Mapa de Fincas" in resp.text
        assert "/mapa" in resp.text

    def test_step_2_field_health(self, client):
        resp = client.get("/demo-fodecijal")
        assert "Salud del Campo" in resp.text

    def test_step_3_ndvi_analysis(self, client):
        resp = client.get("/demo-fodecijal")
        assert "NDVI" in resp.text

    def test_step_4_treatments(self, client):
        resp = client.get("/demo-fodecijal")
        assert "Tratamientos" in resp.text

    def test_step_5_rotation_planner(self, client):
        resp = client.get("/demo-fodecijal")
        assert "Rotacion" in resp.text or "Rotaci" in resp.text

    def test_step_6_carbon_report(self, client):
        resp = client.get("/demo-fodecijal")
        assert "Carbono" in resp.text

    def test_step_7_alert_system(self, client):
        resp = client.get("/demo-fodecijal")
        assert "Alertas" in resp.text

    def test_step_8_whatsapp_demo(self, client):
        resp = client.get("/demo-fodecijal")
        assert "WhatsApp" in resp.text


# -- Link Tests --


class TestDemoLinks:
    """Each step has a valid link to the corresponding page."""

    EXPECTED_LINKS = [
        "/mapa",
        "/campo",
        "/intel",
        "/recomendaciones",
        "/rotacion",
        "/carbono",
        "/historial-alertas",
        "/whatsapp-demo",
    ]

    def test_all_links_present(self, client):
        resp = client.get("/demo-fodecijal")
        for link in self.EXPECTED_LINKS:
            assert f'href="{link}"' in resp.text

    def test_links_have_cta_text(self, client):
        resp = client.get("/demo-fodecijal")
        # Each step should have a call-to-action button
        assert resp.text.count("Ir a") >= 8 or resp.text.count("Ver") >= 8


# -- Spanish Labels Tests --


class TestSpanishLabels:
    """All text is in Spanish as required for farmer-facing UI."""

    def test_main_heading_spanish(self, client):
        resp = client.get("/demo-fodecijal")
        assert "Recorrido FODECIJAL" in resp.text or "Demo FODECIJAL" in resp.text

    def test_progress_label_spanish(self, client):
        resp = client.get("/demo-fodecijal")
        assert "Progreso" in resp.text or "pasos" in resp.text

    def test_step_descriptions_spanish(self, client):
        resp = client.get("/demo-fodecijal")
        # Should have Spanish descriptions, not English
        assert "inteligencia" in resp.text.lower() or "agricultura" in resp.text.lower()

    def test_no_english_headings(self, client):
        resp = client.get("/demo-fodecijal")
        text = resp.text
        # Should not have English-only section headings
        assert "Farm Map" not in text
        assert "Field Health" not in text
        assert "Alert System" not in text


# -- Completion Tracking Tests --


class TestCompletionTracking:
    """Steps have checkmark elements for tracking completion."""

    def test_steps_have_checkmarks(self, client):
        resp = client.get("/demo-fodecijal")
        # Each step should have a checkbox or checkmark element
        assert 'class="step-check"' in resp.text or 'data-step=' in resp.text

    def test_steps_have_step_numbers(self, client):
        resp = client.get("/demo-fodecijal")
        for i in range(1, 9):
            assert f"Paso {i}" in resp.text or f'data-step="{i}"' in resp.text


# -- Stats Strip Tests --


class TestStatsStrip:
    """Page has a stats strip with demo overview metrics."""

    def test_has_stats_strip(self, client):
        resp = client.get("/demo-fodecijal")
        assert 'id="demo-stats"' in resp.text or 'class="stats-strip"' in resp.text

    def test_stats_show_step_count(self, client):
        resp = client.get("/demo-fodecijal")
        assert "8" in resp.text  # 8 steps total


# -- Script Tests --


class TestDemoScript:
    """Page loads the demo JavaScript file."""

    def test_loads_js_file(self, client):
        resp = client.get("/demo-fodecijal")
        assert "demo-fodecijal.js" in resp.text
