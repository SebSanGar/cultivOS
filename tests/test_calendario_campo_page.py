"""Tests for the field crop calendar page at /calendario-campo (#242).

Router-disjoint FileResponse route; consumes existing
GET /api/farms/{farm_id}/fields/{field_id}/calendar?year=.
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


class TestCalendarioCampoPage:
    def test_page_returns_200(self, client):
        resp = client.get("/calendario-campo")
        assert resp.status_code == 200

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/calendario-campo")
        html = resp.text
        assert "Finca" in html
        assert "Campo" in html or "campo" in html
        assert "Calendario" in html

    def test_page_has_farm_field_cascade(self, client):
        resp = client.get("/calendario-campo")
        html = resp.text
        assert 'id="cal-farm-select"' in html
        assert 'id="cal-field-select"' in html

    def test_page_has_year_picker(self, client):
        resp = client.get("/calendario-campo")
        assert 'id="cal-year-select"' in resp.text

    def test_page_has_twelve_month_grid(self, client):
        resp = client.get("/calendario-campo")
        assert 'id="cal-grid"' in resp.text

    def test_page_has_total_events_kpi(self, client):
        resp = client.get("/calendario-campo")
        assert 'id="cal-total-events"' in resp.text

    def test_page_has_busiest_month_display(self, client):
        resp = client.get("/calendario-campo")
        assert 'id="cal-busiest-month"' in resp.text

    def test_page_has_event_count_rendering(self, client):
        resp = client.get("/calendario-campo.js")
        js = resp.text
        assert "total_events" in js
        assert "busiest_month" in js

    def test_page_calls_calendar_endpoint(self, client):
        resp = client.get("/calendario-campo.js")
        assert resp.status_code == 200
        assert "/calendar" in resp.text

    def test_js_file_served(self, client):
        resp = client.get("/calendario-campo.js")
        assert resp.status_code == 200
