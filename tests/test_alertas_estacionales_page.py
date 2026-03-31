"""Tests for the seasonal TEK alerts page at /alertas-estacionales."""

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Farm
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


def _seed_farm(db):
    farm = Farm(name="Rancho TEK", state="Jalisco", total_hectares=40.0)
    db.add(farm)
    db.commit()
    return farm


# -- Page Load Tests --


class TestAlertasEstacionalesPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/alertas-estacionales")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/alertas-estacionales")
        assert "Inteligencia Ancestral" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/alertas-estacionales")
        assert 'id="seasonal-farm-select"' in resp.text

    def test_page_has_empty_state(self, client):
        resp = client.get("/alertas-estacionales")
        assert 'id="seasonal-empty"' in resp.text

    def test_page_has_content_container(self, client):
        resp = client.get("/alertas-estacionales")
        assert 'id="seasonal-content"' in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/alertas-estacionales")
        assert 'id="seasonal-stats"' in resp.text

    def test_page_has_alerts_grid(self, client):
        resp = client.get("/alertas-estacionales")
        assert 'id="seasonal-alerts"' in resp.text

    def test_page_has_js_script(self, client):
        resp = client.get("/alertas-estacionales")
        assert "alertas-estacionales.js" in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/alertas-estacionales")
        assert "intel-nav" in resp.text

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/alertas-estacionales")
        assert "Seleccione una granja" in resp.text

    def test_page_subtitle_mentions_ancestral(self, client):
        resp = client.get("/alertas-estacionales")
        assert "ancestral" in resp.text.lower()


# -- API Integration Tests --


class TestSeasonalAlertsAPI:
    """Seasonal alerts API returns expected data structure."""

    def test_api_returns_alerts(self, client, db):
        farm = _seed_farm(db)
        resp = client.get(f"/api/farms/{farm.id}/seasonal-alerts")
        assert resp.status_code == 200
        data = resp.json()
        assert "alerts" in data
        assert "season" in data
        assert "farm_id" in data
        assert data["farm_id"] == farm.id

    def test_api_returns_season_name(self, client, db):
        farm = _seed_farm(db)
        resp = client.get(f"/api/farms/{farm.id}/seasonal-alerts")
        data = resp.json()
        assert data["season"] in ["temporal", "secas", "transicion"]

    def test_api_with_reference_date(self, client, db):
        farm = _seed_farm(db)
        resp = client.get(
            f"/api/farms/{farm.id}/seasonal-alerts",
            params={"reference_date": "2026-07-15"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["reference_date"] == "2026-07-15"

    def test_api_alerts_have_type(self, client, db):
        farm = _seed_farm(db)
        resp = client.get(f"/api/farms/{farm.id}/seasonal-alerts")
        data = resp.json()
        if data["alerts"]:
            alert = data["alerts"][0]
            assert "alert_type" in alert or "type" in alert

    def test_api_404_for_missing_farm(self, client):
        resp = client.get("/api/farms/9999/seasonal-alerts")
        assert resp.status_code == 404
