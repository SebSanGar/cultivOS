"""Tests for the field disease history page at /historial-enfermedades (#215)."""

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


class TestDiseaseHistoryPage:
    def test_page_returns_200(self, client):
        resp = client.get("/historial-enfermedades")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/historial-enfermedades")
        assert "Historial" in resp.text or "Enfermedades" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/historial-enfermedades")
        assert 'id="dh-farm-select"' in resp.text

    def test_page_has_field_selector(self, client):
        resp = client.get("/historial-enfermedades")
        assert 'id="dh-field-select"' in resp.text

    def test_page_has_chart_canvas(self, client):
        resp = client.get("/historial-enfermedades")
        assert 'id="dh-chart"' in resp.text

    def test_page_has_recurring_list(self, client):
        resp = client.get("/historial-enfermedades")
        assert 'id="dh-recurring"' in resp.text

    def test_page_has_free_counter(self, client):
        resp = client.get("/historial-enfermedades")
        assert 'id="dh-free-counter"' in resp.text

    def test_page_includes_chartjs(self, client):
        resp = client.get("/historial-enfermedades")
        assert "chart.js" in resp.text.lower() or "chart.umd" in resp.text.lower()

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/historial-enfermedades")
        html = resp.text
        assert "Finca" in html
        assert "Parcela" in html or "Campo" in html

    def test_page_includes_js_script(self, client):
        resp = client.get("/historial-enfermedades")
        assert "historial-enfermedades.js" in resp.text
