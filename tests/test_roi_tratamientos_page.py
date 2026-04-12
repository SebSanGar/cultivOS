"""Tests for the farm treatment ROI page at /roi-tratamientos (#222).

Router-disjoint FileResponse route; consumes existing
GET /api/farms/{farm_id}/treatment-roi (#203).
"""

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


class TestRoiTratamientosPage:
    def test_page_returns_200(self, client):
        resp = client.get("/roi-tratamientos")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/roi-tratamientos")
        assert "ROI" in resp.text or "Retorno" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/roi-tratamientos")
        assert 'id="roi-farm-select"' in resp.text

    def test_page_has_kpi_strip(self, client):
        resp = client.get("/roi-tratamientos")
        html = resp.text
        assert 'id="roi-best-treatment"' in html
        assert 'id="roi-worst-treatment"' in html
        assert 'id="roi-recommendation-pill"' in html

    def test_page_has_table_container(self, client):
        resp = client.get("/roi-tratamientos")
        html = resp.text
        assert 'id="roi-table-body"' in html
        # Table columns: treatment, cost_per_health_point, health_delta, positive_followup_count
        assert "cost_per_health_point" in html.lower() or "costo por punto" in html.lower() or "costo/punto" in html.lower()

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/roi-tratamientos")
        html = resp.text
        assert "Finca" in html
        assert "Tratamiento" in html or "tratamiento" in html

    def test_page_includes_js_script(self, client):
        resp = client.get("/roi-tratamientos")
        assert "roi-tratamientos.js" in resp.text

    def test_js_calls_treatment_roi_endpoint(self, client):
        resp = client.get("/roi-tratamientos.js")
        assert resp.status_code == 200
        assert "/treatment-roi" in resp.text

    def test_js_has_recommendation_pill_tiers(self, client):
        """Four Spanish recommendation pill classes: excelente/buena/cuestionable/sin mejora."""
        resp = client.get("/roi-tratamientos.js")
        text = resp.text.lower()
        assert "excelente" in text
        assert "buena" in text
        assert "cuestionable" in text
        assert "sin mejora" in text or "sin-mejora" in text

    def test_js_loads_farms_and_calls_roi(self, client):
        resp = client.get("/roi-tratamientos.js")
        text = resp.text
        assert "/api/farms" in text
        assert "roi-farm-select" in text
