"""Tests for the cooperative FODECIJAL evidence pack page at /coop-evidencia (#213)."""

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


class TestCoopEvidencePageLoad:
    def test_page_returns_200(self, client):
        resp = client.get("/coop-evidencia")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/coop-evidencia")
        assert "Evidencia" in resp.text or "evidencia" in resp.text.lower()

    def test_page_has_coop_selector(self, client):
        resp = client.get("/coop-evidencia")
        assert 'id="coop-evidence-select"' in resp.text

    def test_page_has_readiness_kpi(self, client):
        resp = client.get("/coop-evidencia")
        assert 'id="coop-evidence-readiness"' in resp.text

    def test_page_has_health_kpi(self, client):
        resp = client.get("/coop-evidencia")
        assert 'id="coop-evidence-health"' in resp.text

    def test_page_has_regen_kpi(self, client):
        resp = client.get("/coop-evidencia")
        assert 'id="coop-evidence-regen"' in resp.text

    def test_page_has_co2e_kpi(self, client):
        resp = client.get("/coop-evidencia")
        assert 'id="coop-evidence-co2e"' in resp.text

    def test_page_has_diversity_kpi(self, client):
        resp = client.get("/coop-evidencia")
        assert 'id="coop-evidence-diversity"' in resp.text

    def test_page_has_strength_block(self, client):
        resp = client.get("/coop-evidencia")
        assert 'id="coop-evidence-strength"' in resp.text

    def test_page_has_weakness_block(self, client):
        resp = client.get("/coop-evidencia")
        assert 'id="coop-evidence-weakness"' in resp.text

    def test_page_has_outbreak_pill(self, client):
        resp = client.get("/coop-evidencia")
        assert 'id="coop-evidence-outbreak"' in resp.text

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/coop-evidencia")
        html = resp.text
        assert "Cooperativa" in html
        assert "Seleccione" in html

    def test_page_has_js_script(self, client):
        resp = client.get("/coop-evidencia")
        assert "coop-evidencia.js" in resp.text

    def test_js_file_served(self, client):
        resp = client.get("/coop-evidencia.js")
        assert resp.status_code == 200
        body = resp.text
        assert "/api/cooperatives/" in body
        assert "evidence-pack" in body
