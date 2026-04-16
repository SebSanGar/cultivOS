"""Tests for the field weather alert history page at /alertas-clima (#241).

Router-disjoint FileResponse route; consumes existing
GET /api/farms/{farm_id}/fields/{field_id}/weather-alert-history.
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


class TestAlertasClimaPage:
    def test_page_returns_200(self, client):
        resp = client.get("/alertas-clima")
        assert resp.status_code == 200

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/alertas-clima")
        html = resp.text
        assert "Alertas" in html or "alertas" in html
        assert "Clima" in html or "clima" in html

    def test_page_has_farm_and_field_cascade(self, client):
        resp = client.get("/alertas-clima")
        html = resp.text
        assert 'id="ac-farm-select"' in html
        assert 'id="ac-field-select"' in html

    def test_page_has_days_selector(self, client):
        resp = client.get("/alertas-clima")
        html = resp.text
        assert 'id="ac-days-select"' in html
        for days in ("30", "60", "90", "180", "365"):
            assert f'value="{days}"' in html

    def test_page_has_total_alerts_kpi(self, client):
        resp = client.get("/alertas-clima")
        assert 'id="ac-total-alerts"' in resp.text

    def test_page_has_trend_pill(self, client):
        resp = client.get("/alertas-clima")
        assert 'id="ac-trend-pill"' in resp.text

    def test_page_has_chart_canvas(self, client):
        resp = client.get("/alertas-clima")
        html = resp.text
        assert 'id="ac-chart"' in html
        assert "<canvas" in html

    def test_js_calls_weather_alert_history_endpoint(self, client):
        resp = client.get("/alertas-clima.js")
        assert resp.status_code == 200
        assert "/weather-alert-history" in resp.text

    def test_js_handles_empty_data(self, client):
        resp = client.get("/alertas-clima.js")
        js = resp.text.lower()
        assert "sin datos" in js or "sin alertas" in js or "no-data" in js

    def test_js_file_served(self, client):
        resp = client.get("/alertas-clima.js")
        assert resp.status_code == 200
        assert "fetch" in resp.text
