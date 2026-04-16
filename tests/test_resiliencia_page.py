"""Tests for the field crop resilience page at /resiliencia (#234).

Router-disjoint FileResponse route; consumes existing
GET /api/farms/{farm_id}/fields/{field_id}/resilience-score.
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


class TestResilienciaPage:
    def test_page_returns_200(self, client):
        resp = client.get("/resiliencia")
        assert resp.status_code == 200

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/resiliencia")
        html = resp.text
        assert "Finca" in html
        assert "Campo" in html or "campo" in html

    def test_page_has_farm_selector(self, client):
        resp = client.get("/resiliencia")
        assert 'id="res-farm-select"' in resp.text

    def test_page_has_field_selector(self, client):
        resp = client.get("/resiliencia")
        assert 'id="res-field-select"' in resp.text

    def test_page_has_score_display(self, client):
        resp = client.get("/resiliencia")
        assert 'id="res-score"' in resp.text

    def test_page_has_component_bars(self, client):
        resp = client.get("/resiliencia")
        html = resp.text
        assert 'id="res-bar-health"' in html
        assert 'id="res-bar-soil-ph"' in html
        assert 'id="res-bar-water-stress"' in html
        assert 'id="res-bar-disease-risk"' in html

    def test_page_has_grade_pill(self, client):
        resp = client.get("/resiliencia")
        assert 'id="res-grade-pill"' in resp.text

    def test_page_calls_resilience_score_endpoint(self, client):
        resp = client.get("/resiliencia.js")
        assert resp.status_code == 200
        assert "/resilience-score" in resp.text

    def test_page_has_empty_data_branch(self, client):
        resp = client.get("/resiliencia.js")
        js = resp.text
        assert "sin datos" in js.lower() or "Sin datos" in js or "no-data" in js.lower()

    def test_page_has_title(self, client):
        resp = client.get("/resiliencia")
        assert "Resiliencia" in resp.text
