"""Tests for the cooperative monthly progress page at /coop-progreso-mensual (#214)."""

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


class TestCoopMonthlyProgressPage:
    def test_page_returns_200(self, client):
        resp = client.get("/coop-progreso-mensual")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/coop-progreso-mensual")
        assert "Progreso" in resp.text or "progreso" in resp.text.lower()

    def test_page_has_coop_selector(self, client):
        resp = client.get("/coop-progreso-mensual")
        assert 'id="coop-progress-select"' in resp.text

    def test_page_has_chart_canvas(self, client):
        resp = client.get("/coop-progreso-mensual")
        assert 'id="coop-progress-chart"' in resp.text

    def test_page_has_trend_pill(self, client):
        resp = client.get("/coop-progreso-mensual")
        assert 'id="coop-progress-trend"' in resp.text

    def test_page_has_delta_table(self, client):
        resp = client.get("/coop-progreso-mensual")
        assert 'id="coop-progress-deltas"' in resp.text

    def test_page_includes_chartjs(self, client):
        resp = client.get("/coop-progreso-mensual")
        assert "chart.js" in resp.text.lower() or "chart.umd" in resp.text.lower()

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/coop-progreso-mensual")
        html = resp.text
        assert "Cooperativa" in html
        assert "Seleccione" in html

    def test_page_has_js_script(self, client):
        resp = client.get("/coop-progreso-mensual")
        assert "coop-progreso-mensual.js" in resp.text

    def test_js_file_served(self, client):
        resp = client.get("/coop-progreso-mensual.js")
        assert resp.status_code == 200
        body = resp.text
        assert "/api/cooperatives/" in body
        assert "monthly-progress" in body

    def test_js_references_chart_constructor(self, client):
        resp = client.get("/coop-progreso-mensual.js")
        assert "new Chart" in resp.text

    def test_js_references_avg_health_field(self, client):
        resp = client.get("/coop-progreso-mensual.js")
        assert "avg_health" in resp.text

    def test_js_references_regen_score_field(self, client):
        resp = client.get("/coop-progreso-mensual.js")
        assert "regen_score_avg" in resp.text

    def test_js_references_mom_delta_field(self, client):
        resp = client.get("/coop-progreso-mensual.js")
        assert "mom_delta" in resp.text
