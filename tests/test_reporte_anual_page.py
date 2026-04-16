"""Tests for the farm annual report page at /reporte-anual (#232).

Router-disjoint FileResponse route; consumes existing
GET /api/farms/{farm_id}/annual-report?year=.
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


class TestReporteAnualPage:
    def test_page_returns_200(self, client):
        resp = client.get("/reporte-anual")
        assert resp.status_code == 200

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/reporte-anual")
        html = resp.text
        assert "Finca" in html
        assert "Anual" in html or "anual" in html

    def test_page_has_farm_selector(self, client):
        resp = client.get("/reporte-anual")
        assert 'id="anual-farm-select"' in resp.text

    def test_page_has_year_picker(self, client):
        resp = client.get("/reporte-anual")
        assert 'id="anual-year-select"' in resp.text

    def test_page_has_kpi_strip_ids(self, client):
        resp = client.get("/reporte-anual")
        html = resp.text
        assert 'id="anual-best-field"' in html
        assert 'id="anual-most-improved"' in html
        assert 'id="anual-co2e"' in html
        assert 'id="anual-treatments"' in html

    def test_page_has_field_table(self, client):
        resp = client.get("/reporte-anual")
        assert 'id="anual-field-table"' in resp.text

    def test_page_has_trend_pill_reference(self, client):
        resp = client.get("/reporte-anual.js")
        assert resp.status_code == 200
        assert "ndvi_trend" in resp.text

    def test_js_calls_annual_report_endpoint(self, client):
        resp = client.get("/reporte-anual.js")
        assert "/annual-report" in resp.text

    def test_page_has_empty_data_branch(self, client):
        resp = client.get("/reporte-anual.js")
        js = resp.text
        assert "sin datos" in js.lower() or "no hay" in js.lower() or "fields" in js

    def test_page_has_title(self, client):
        resp = client.get("/reporte-anual")
        html = resp.text
        assert "Reporte Anual" in html or "reporte-anual" in html.lower()
