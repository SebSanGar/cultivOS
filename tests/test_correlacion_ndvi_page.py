"""Tests for the field NDVI-health correlation page at /correlacion-ndvi (#224)."""

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


class TestCorrelacionNdviPage:
    def test_page_returns_200(self, client):
        resp = client.get("/correlacion-ndvi")
        assert resp.status_code == 200

    def test_page_has_spanish_title(self, client):
        resp = client.get("/correlacion-ndvi")
        assert "Correlaci" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/correlacion-ndvi")
        assert 'id="cn-farm-select"' in resp.text

    def test_page_has_field_selector(self, client):
        resp = client.get("/correlacion-ndvi")
        assert 'id="cn-field-select"' in resp.text

    def test_page_has_strength_pill(self, client):
        resp = client.get("/correlacion-ndvi")
        assert 'id="cn-strength-pill"' in resp.text

    def test_page_has_scatter_canvas(self, client):
        resp = client.get("/correlacion-ndvi")
        assert 'id="cn-scatter"' in resp.text

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/correlacion-ndvi")
        html = resp.text
        assert "Finca" in html
        assert "Parcela" in html or "Campo" in html
        assert "NDVI" in html

    def test_page_includes_js_script(self, client):
        resp = client.get("/correlacion-ndvi")
        assert "correlacion-ndvi.js" in resp.text

    def test_js_references_ndvi_correlation_endpoint(self, client):
        resp = client.get("/correlacion-ndvi.js")
        assert "/ndvi-health-correlation" in resp.text

    def test_js_loads_farms(self, client):
        resp = client.get("/correlacion-ndvi.js")
        assert "/api/farms" in resp.text
