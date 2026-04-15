"""Tests for the cooperative FODECIJAL readiness page at /preparacion-fodecijal (#237).

Router-disjoint FileResponse route; consumes existing
GET /api/cooperatives/{coop_id}/fodecijal-readiness (#186).
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


class TestPreparacionFodecijalPage:
    def test_page_returns_200(self, client):
        resp = client.get("/preparacion-fodecijal")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/preparacion-fodecijal")
        assert "FODECIJAL" in resp.text

    def test_page_has_coop_selector(self, client):
        resp = client.get("/preparacion-fodecijal")
        assert 'id="fodecijal-coop-select"' in resp.text

    def test_page_has_readiness_big_number(self, client):
        resp = client.get("/preparacion-fodecijal")
        assert 'id="fodecijal-readiness-score"' in resp.text

    def test_page_has_pillar_bar_ids(self, client):
        resp = client.get("/preparacion-fodecijal")
        html = resp.text
        assert 'id="pillar-data_completeness"' in html
        assert 'id="pillar-regen_score"' in html
        assert 'id="pillar-tek_alignment"' in html
        assert 'id="pillar-sensor_freshness"' in html
        assert 'id="pillar-treatment_effectiveness"' in html

    def test_page_has_grade_pill(self, client):
        resp = client.get("/preparacion-fodecijal")
        assert 'id="fodecijal-grade"' in resp.text

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/preparacion-fodecijal")
        html = resp.text
        assert "Cooperativa" in html
        assert "FODECIJAL" in html

    def test_page_has_empty_coop_branch(self, client):
        resp = client.get("/preparacion-fodecijal")
        html = resp.text
        js_resp = client.get("/preparacion-fodecijal.js")
        combined = html + js_resp.text
        assert "Seleccione" in combined or "seleccione" in combined

    def test_page_includes_js_script(self, client):
        resp = client.get("/preparacion-fodecijal")
        assert "preparacion-fodecijal.js" in resp.text

    def test_js_calls_fodecijal_readiness_endpoint(self, client):
        resp = client.get("/preparacion-fodecijal.js")
        assert resp.status_code == 200
        assert "/fodecijal-readiness" in resp.text
