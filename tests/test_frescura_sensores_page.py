"""Tests for the sensor data freshness page at /frescura-sensores (#229).

Router-disjoint FileResponse route; consumes existing
GET /api/farms/{farm_id}/sensor-freshness (#175).
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


class TestFrescuraSensoresPage:
    def test_page_returns_200(self, client):
        resp = client.get("/frescura-sensores")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/frescura-sensores")
        assert "Frescura" in resp.text or "Sensores" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/frescura-sensores")
        assert 'id="freshness-farm-select"' in resp.text

    def test_page_has_sensor_grid_table(self, client):
        resp = client.get("/frescura-sensores")
        assert 'id="freshness-grid"' in resp.text

    def test_page_has_freshness_color_classes(self, client):
        resp = client.get("/frescura-sensores")
        html = resp.text
        js_resp = client.get("/frescura-sensores.js")
        combined = html + js_resp.text
        assert "fresh-green" in combined or "fresh-amber" in combined or "fresh-red" in combined or "#22c55e" in combined

    def test_page_has_stale_count_kpi(self, client):
        resp = client.get("/frescura-sensores")
        assert 'id="freshness-stale-count"' in resp.text

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/frescura-sensores")
        html = resp.text
        assert "Finca" in html
        assert "Sensores" in html or "sensores" in html

    def test_page_has_empty_data_branch(self, client):
        resp = client.get("/frescura-sensores")
        html = resp.text
        js_resp = client.get("/frescura-sensores.js")
        combined = html + js_resp.text
        assert "Seleccione" in combined or "seleccione" in combined

    def test_page_includes_js_script(self, client):
        resp = client.get("/frescura-sensores")
        assert "frescura-sensores.js" in resp.text

    def test_js_calls_sensor_freshness_endpoint(self, client):
        resp = client.get("/frescura-sensores.js")
        assert resp.status_code == 200
        assert "/sensor-freshness" in resp.text
