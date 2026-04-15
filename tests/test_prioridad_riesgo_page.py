"""Tests for the risk-weighted field priority page at /prioridad-riesgo (#228).

Router-disjoint FileResponse route; consumes existing
GET /api/farms/{farm_id}/risk-priority (#180).
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


class TestPrioridadRiesgoPage:
    def test_page_returns_200(self, client):
        resp = client.get("/prioridad-riesgo")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/prioridad-riesgo")
        assert "Prioridad" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/prioridad-riesgo")
        assert 'id="risk-farm-select"' in resp.text

    def test_page_has_field_card_container(self, client):
        resp = client.get("/prioridad-riesgo")
        assert 'id="risk-field-cards"' in resp.text

    def test_page_has_risk_score_display(self, client):
        resp = client.get("/prioridad-riesgo")
        assert "risk_score" in resp.text.lower() or "priority_score" in resp.text.lower() or "puntuación" in resp.text.lower()

    def test_page_has_color_urgency_classes(self, client):
        resp = client.get("/prioridad-riesgo")
        html = resp.text
        js_resp = client.get("/prioridad-riesgo.js")
        combined = html + js_resp.text
        assert "risk-red" in combined or "urgency-red" in combined or "#ef4444" in combined or "red" in combined.lower()

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/prioridad-riesgo")
        html = resp.text
        assert "Finca" in html
        assert "Campo" in html or "campo" in html

    def test_page_includes_js_script(self, client):
        resp = client.get("/prioridad-riesgo")
        assert "prioridad-riesgo.js" in resp.text

    def test_js_calls_risk_priority_endpoint(self, client):
        resp = client.get("/prioridad-riesgo.js")
        assert resp.status_code == 200
        assert "/risk-priority" in resp.text

    def test_js_loads_farms(self, client):
        resp = client.get("/prioridad-riesgo.js")
        text = resp.text
        assert "/api/farms" in text
        assert "risk-farm-select" in text
