"""Tests for the field health prediction page at /prediccion-salud (#238).

Router-disjoint FileResponse route; consumes existing
GET /api/farms/{farm_id}/fields/{field_id}/health-prediction.
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


class TestPrediccionSaludPage:
    def test_page_returns_200(self, client):
        resp = client.get("/prediccion-salud")
        assert resp.status_code == 200

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/prediccion-salud")
        html = resp.text
        assert "Finca" in html
        assert "Campo" in html or "campo" in html

    def test_page_has_farm_selector(self, client):
        resp = client.get("/prediccion-salud")
        assert 'id="pred-farm-select"' in resp.text

    def test_page_has_field_selector(self, client):
        resp = client.get("/prediccion-salud")
        assert 'id="pred-field-select"' in resp.text

    def test_page_has_current_score_display(self, client):
        resp = client.get("/prediccion-salud")
        assert 'id="pred-current-score"' in resp.text

    def test_page_has_predicted_score_display(self, client):
        resp = client.get("/prediccion-salud")
        assert 'id="pred-predicted-score"' in resp.text

    def test_page_has_trend_arrow(self, client):
        resp = client.get("/prediccion-salud")
        assert 'id="pred-trend-arrow"' in resp.text

    def test_page_has_confidence_pill(self, client):
        resp = client.get("/prediccion-salud")
        assert 'id="pred-confidence-pill"' in resp.text

    def test_page_has_risk_flag_element(self, client):
        resp = client.get("/prediccion-salud")
        assert 'id="pred-risk-flag"' in resp.text

    def test_js_calls_health_prediction_endpoint(self, client):
        resp = client.get("/prediccion-salud.js")
        assert resp.status_code == 200
        assert "/health-prediction" in resp.text
