"""Tests for the cooperative crop diversity page at /diversidad-cultivos (#231).

Router-disjoint FileResponse route; consumes existing
GET /api/cooperatives/{coop_id}/crop-diversity (#199).
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


class TestDiversidadCultivosPage:
    def test_page_returns_200(self, client):
        resp = client.get("/diversidad-cultivos")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/diversidad-cultivos")
        assert "Diversidad" in resp.text

    def test_page_has_coop_selector(self, client):
        resp = client.get("/diversidad-cultivos")
        assert 'id="diversity-coop-select"' in resp.text

    def test_page_has_shannon_index_display(self, client):
        resp = client.get("/diversidad-cultivos")
        assert 'id="diversity-shannon"' in resp.text

    def test_page_has_bar_chart_canvas(self, client):
        resp = client.get("/diversidad-cultivos")
        assert 'id="diversity-bar-chart"' in resp.text

    def test_page_has_per_farm_table(self, client):
        resp = client.get("/diversidad-cultivos")
        assert 'id="diversity-farm-table"' in resp.text

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/diversidad-cultivos")
        html = resp.text
        assert "Cooperativa" in html
        assert "Diversidad" in html

    def test_page_has_empty_data_branch(self, client):
        resp = client.get("/diversidad-cultivos")
        html = resp.text
        js_resp = client.get("/diversidad-cultivos.js")
        combined = html + js_resp.text
        assert "Seleccione" in combined or "seleccione" in combined

    def test_page_includes_js_script(self, client):
        resp = client.get("/diversidad-cultivos")
        assert "diversidad-cultivos.js" in resp.text

    def test_js_calls_crop_diversity_endpoint(self, client):
        resp = client.get("/diversidad-cultivos.js")
        assert resp.status_code == 200
        assert "/crop-diversity" in resp.text
