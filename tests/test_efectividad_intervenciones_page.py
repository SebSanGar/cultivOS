"""Tests for the field intervention effectiveness page at /efectividad-intervenciones (#225)."""

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


class TestEfectividadIntervencionesPage:
    def test_page_returns_200(self, client):
        resp = client.get("/efectividad-intervenciones")
        assert resp.status_code == 200

    def test_page_has_spanish_title(self, client):
        resp = client.get("/efectividad-intervenciones")
        assert "Efectividad" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/efectividad-intervenciones")
        assert 'id="ei-farm-select"' in resp.text

    def test_page_has_field_selector(self, client):
        resp = client.get("/efectividad-intervenciones")
        assert 'id="ei-field-select"' in resp.text

    def test_page_has_donut_canvas(self, client):
        resp = client.get("/efectividad-intervenciones")
        assert 'id="ei-donut"' in resp.text

    def test_page_has_effectiveness_rate_kpi(self, client):
        resp = client.get("/efectividad-intervenciones")
        assert 'id="ei-effectiveness-rate"' in resp.text

    def test_page_has_best_worst_cards(self, client):
        resp = client.get("/efectividad-intervenciones")
        html = resp.text
        assert 'id="ei-best-treatment"' in html
        assert 'id="ei-worst-treatment"' in html

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/efectividad-intervenciones")
        html = resp.text
        assert "Finca" in html
        assert "Parcela" in html or "Campo" in html

    def test_page_includes_js_script(self, client):
        resp = client.get("/efectividad-intervenciones")
        assert "efectividad-intervenciones.js" in resp.text

    def test_js_references_intervention_effectiveness_endpoint(self, client):
        resp = client.get("/efectividad-intervenciones.js")
        assert "/intervention-effectiveness" in resp.text
