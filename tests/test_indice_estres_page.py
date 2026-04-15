"""Tests for the field stress composite index page at /indice-estres (#233).

Router-disjoint FileResponse route; consumes existing
GET /api/farms/{farm_id}/fields/{field_id}/stress-index.
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


class TestIndiceEstresPage:
    def test_page_returns_200(self, client):
        resp = client.get("/indice-estres")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/indice-estres")
        assert "Índice" in resp.text or "Indice" in resp.text or "Estrés" in resp.text

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/indice-estres")
        html = resp.text
        assert "Finca" in html
        assert "Campo" in html or "campo" in html

    def test_page_has_farm_selector(self, client):
        resp = client.get("/indice-estres")
        assert 'id="stress-farm-select"' in resp.text

    def test_page_has_field_selector(self, client):
        resp = client.get("/indice-estres")
        assert 'id="stress-field-select"' in resp.text

    def test_page_has_stress_big_number(self, client):
        resp = client.get("/indice-estres")
        assert 'id="stress-big-number"' in resp.text

    def test_page_has_three_sub_score_elements(self, client):
        resp = client.get("/indice-estres")
        html = resp.text
        assert 'id="stress-water"' in html
        assert 'id="stress-disease"' in html
        assert 'id="stress-thermal"' in html

    def test_page_has_classification_pill(self, client):
        resp = client.get("/indice-estres")
        assert 'id="stress-level-pill"' in resp.text

    def test_js_calls_stress_index_endpoint(self, client):
        resp = client.get("/indice-estres.js")
        assert resp.status_code == 200
        assert "/stress-index" in resp.text

    def test_page_includes_js_script(self, client):
        resp = client.get("/indice-estres")
        assert "indice-estres.js" in resp.text
