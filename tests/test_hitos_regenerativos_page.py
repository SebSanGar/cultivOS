"""Tests for the farm regen milestones page at /hitos-regenerativos (#223).

Router-disjoint FileResponse route; consumes existing
GET /api/farms/{farm_id}/regen-milestones (#210).
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


class TestHitosRegenerativosPage:
    def test_page_returns_200(self, client):
        resp = client.get("/hitos-regenerativos")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/hitos-regenerativos")
        assert "Hitos" in resp.text or "Regenerativ" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/hitos-regenerativos")
        assert 'id="hitos-farm-select"' in resp.text

    def test_page_has_milestone_containers(self, client):
        resp = client.get("/hitos-regenerativos")
        html = resp.text
        assert 'id="hitos-milestones"' in html

    def test_page_has_progress_bar(self, client):
        resp = client.get("/hitos-regenerativos")
        assert 'id="hitos-progress-bar"' in resp.text

    def test_page_has_next_milestone_hint(self, client):
        resp = client.get("/hitos-regenerativos")
        assert 'id="hitos-next-milestone"' in resp.text

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/hitos-regenerativos")
        html = resp.text
        assert "Finca" in html
        assert "Progreso" in html or "progreso" in html

    def test_page_includes_js_script(self, client):
        resp = client.get("/hitos-regenerativos")
        assert "hitos-regenerativos.js" in resp.text

    def test_js_calls_regen_milestones_endpoint(self, client):
        resp = client.get("/hitos-regenerativos.js")
        assert resp.status_code == 200
        assert "/regen-milestones" in resp.text

    def test_js_loads_farms_and_has_achieved_logic(self, client):
        resp = client.get("/hitos-regenerativos.js")
        text = resp.text
        assert "/api/farms" in text
        assert "achieved" in text
