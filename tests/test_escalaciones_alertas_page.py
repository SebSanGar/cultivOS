"""Tests for the alert escalation backlog page at /escalaciones-alertas (#230).

Router-disjoint FileResponse route; consumes existing
GET /api/farms/{farm_id}/alert-escalations?days=30 (#197).
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


class TestEscalacionesAlertasPage:
    def test_page_returns_200(self, client):
        resp = client.get("/escalaciones-alertas")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/escalaciones-alertas")
        assert "Escalaciones" in resp.text or "Alertas" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/escalaciones-alertas")
        assert 'id="escalation-farm-select"' in resp.text

    def test_page_has_escalation_table(self, client):
        resp = client.get("/escalaciones-alertas")
        assert 'id="escalation-table"' in resp.text

    def test_page_has_severity_pill_classes(self, client):
        resp = client.get("/escalaciones-alertas")
        html = resp.text
        js_resp = client.get("/escalaciones-alertas.js")
        combined = html + js_resp.text
        assert "severity-critical" in combined or "severity-high" in combined or "severity-medium" in combined

    def test_page_has_kpi_elements(self, client):
        resp = client.get("/escalaciones-alertas")
        html = resp.text
        assert 'id="escalation-total"' in html
        assert 'id="escalation-critical-count"' in html

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/escalaciones-alertas")
        html = resp.text
        assert "Finca" in html
        assert "Escalaciones" in html or "escalaciones" in html

    def test_page_has_empty_data_branch(self, client):
        resp = client.get("/escalaciones-alertas")
        html = resp.text
        js_resp = client.get("/escalaciones-alertas.js")
        combined = html + js_resp.text
        assert "Seleccione" in combined or "seleccione" in combined

    def test_page_includes_js_script(self, client):
        resp = client.get("/escalaciones-alertas")
        assert "escalaciones-alertas.js" in resp.text

    def test_js_calls_alert_escalations_endpoint(self, client):
        resp = client.get("/escalaciones-alertas.js")
        assert resp.status_code == 200
        assert "/alert-escalations" in resp.text
