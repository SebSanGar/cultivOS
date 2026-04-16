"""Tests for the cooperative member ranking page at /ranking-miembros (#236).

Router-disjoint FileResponse route; consumes existing
GET /api/cooperatives/{coop_id}/member-ranking.
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


class TestRankingMiembrosPage:
    def test_page_returns_200(self, client):
        resp = client.get("/ranking-miembros")
        assert resp.status_code == 200

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/ranking-miembros")
        html = resp.text
        assert "Cooperativa" in html or "cooperativa" in html
        assert "Ranking" in html or "ranking" in html

    def test_page_has_coop_selector(self, client):
        resp = client.get("/ranking-miembros")
        assert 'id="rank-coop-select"' in resp.text

    def test_page_has_farm_card_container(self, client):
        resp = client.get("/ranking-miembros")
        assert 'id="rank-cards"' in resp.text

    def test_page_has_composite_score_display(self, client):
        resp = client.get("/ranking-miembros.js")
        assert "composite_score" in resp.text or "Puntaje" in resp.text

    def test_page_has_medal_badges_for_top3(self, client):
        resp = client.get("/ranking-miembros.js")
        js = resp.text
        assert "medal" in js.lower() or "medalla" in js.lower() or "#ffd700" in js or "#c0c0c0" in js or "#cd7f32" in js

    def test_page_calls_member_ranking_endpoint(self, client):
        resp = client.get("/ranking-miembros.js")
        assert resp.status_code == 200
        assert "/member-ranking" in resp.text

    def test_page_handles_empty_coop(self, client):
        resp = client.get("/ranking-miembros.js")
        js = resp.text
        assert "sin datos" in js.lower() or "Sin datos" in js or "no-data" in js.lower() or "no hay" in js.lower()

    def test_js_file_served(self, client):
        resp = client.get("/ranking-miembros.js")
        assert resp.status_code == 200
        assert "fetch" in resp.text

    def test_page_has_title(self, client):
        resp = client.get("/ranking-miembros")
        assert "Ranking" in resp.text
