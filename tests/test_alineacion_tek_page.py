"""Tests for the field TEK sensor alignment page at /alineacion-tek (#240).

Router-disjoint FileResponse route; consumes existing
GET /api/farms/{farm_id}/fields/{field_id}/tek-alignment?month=.
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


class TestAlineacionTekPage:
    def test_page_returns_200(self, client):
        resp = client.get("/alineacion-tek")
        assert resp.status_code == 200

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/alineacion-tek")
        html = resp.text
        assert "Finca" in html
        assert "Campo" in html or "campo" in html

    def test_page_has_farm_field_cascade(self, client):
        resp = client.get("/alineacion-tek")
        html = resp.text
        assert 'id="tek-farm-select"' in html
        assert 'id="tek-field-select"' in html

    def test_page_has_month_selector(self, client):
        resp = client.get("/alineacion-tek")
        assert 'id="tek-month-select"' in resp.text

    def test_page_has_alignment_score_display(self, client):
        resp = client.get("/alineacion-tek")
        assert 'id="tek-score"' in resp.text

    def test_page_has_practice_card_container(self, client):
        resp = client.get("/alineacion-tek")
        assert 'id="tek-practices"' in resp.text

    def test_page_has_sensor_support_indicator(self, client):
        resp = client.get("/alineacion-tek.js")
        js = resp.text
        assert "sensor_support" in js

    def test_page_has_evidence_text(self, client):
        resp = client.get("/alineacion-tek.js")
        js = resp.text
        assert "evidence_es" in js

    def test_page_calls_tek_alignment_endpoint(self, client):
        resp = client.get("/alineacion-tek.js")
        assert resp.status_code == 200
        assert "/tek-alignment" in resp.text

    def test_js_file_served(self, client):
        resp = client.get("/alineacion-tek.js")
        assert resp.status_code == 200
