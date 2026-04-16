"""Tests for the field weekly action plan page at /plan-accion (#239).

Router-disjoint FileResponse route; consumes existing
GET /api/farms/{farm_id}/fields/{field_id}/action-plan?days=7.
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


class TestPlanAccionPage:
    def test_page_returns_200(self, client):
        resp = client.get("/plan-accion")
        assert resp.status_code == 200

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/plan-accion")
        html = resp.text
        assert "Finca" in html
        assert "Campo" in html or "campo" in html

    def test_page_has_farm_selector(self, client):
        resp = client.get("/plan-accion")
        assert 'id="accion-farm-select"' in resp.text

    def test_page_has_field_selector(self, client):
        resp = client.get("/plan-accion")
        assert 'id="accion-field-select"' in resp.text

    def test_page_has_action_count_kpi(self, client):
        resp = client.get("/plan-accion")
        assert 'id="accion-count"' in resp.text

    def test_page_has_action_card_container(self, client):
        resp = client.get("/plan-accion")
        assert 'id="accion-cards"' in resp.text

    def test_page_has_priority_badge_reference(self, client):
        resp = client.get("/plan-accion.js")
        assert resp.status_code == 200
        assert "priority" in resp.text

    def test_page_has_source_indicator_reference(self, client):
        resp = client.get("/plan-accion.js")
        assert "category" in resp.text or "source" in resp.text

    def test_js_calls_action_plan_endpoint(self, client):
        resp = client.get("/plan-accion.js")
        assert "/action-plan" in resp.text

    def test_page_has_title(self, client):
        resp = client.get("/plan-accion")
        html = resp.text
        assert "Plan de Acci" in html or "plan-accion" in html.lower()
