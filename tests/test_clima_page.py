"""Tests for the weather dashboard page at /clima."""

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
    farm = Farm(
        name="Rancho El Sol", state="Jalisco", total_hectares=100.0,
        location_lat=20.6597, location_lon=-103.3496, municipality="Zapopan"
    )
    db.add(farm)
    db.commit()
    return farm


# -- Page Load Tests --


class TestClimaPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/clima")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/clima")
        assert "Panel Climatico" in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/clima")
        assert "intel-nav" in resp.text

    def test_page_has_script(self, client):
        resp = client.get("/clima")
        assert "clima.js" in resp.text

    def test_page_has_footer(self, client):
        resp = client.get("/clima")
        assert "cultivos-footer" in resp.text

    def test_page_has_meta_description(self, client):
        resp = client.get("/clima")
        assert "pronostico" in resp.text.lower()


# -- DOM Elements Tests --


class TestClimaDOMElements:
    """Key DOM elements exist for JS weather rendering."""

    def test_farm_selector_exists(self, client):
        resp = client.get("/clima")
        assert 'id="clima-farm-select"' in resp.text

    def test_current_conditions_strip(self, client):
        resp = client.get("/clima")
        assert 'id="clima-current"' in resp.text
        assert 'id="clima-temp"' in resp.text
        assert 'id="clima-humidity"' in resp.text
        assert 'id="clima-wind"' in resp.text
        assert 'id="clima-rain"' in resp.text

    def test_drought_alert_banner(self, client):
        resp = client.get("/clima")
        assert 'id="clima-drought-alert"' in resp.text
        assert 'id="clima-drought-msg"' in resp.text

    def test_forecast_container(self, client):
        resp = client.get("/clima")
        assert 'id="clima-forecast"' in resp.text

    def test_temperature_chart(self, client):
        resp = client.get("/clima")
        assert 'id="clima-temp-chart"' in resp.text

    def test_rainfall_chart(self, client):
        resp = client.get("/clima")
        assert 'id="clima-rain-chart"' in resp.text

    def test_history_container(self, client):
        resp = client.get("/clima")
        assert 'id="clima-history"' in resp.text

    def test_spanish_labels(self, client):
        resp = client.get("/clima")
        text = resp.text
        assert "Temperatura" in text
        assert "Humedad" in text
        assert "Precipitacion" in text


# -- API Integration Tests --


class TestClimaAPIIntegration:
    """API endpoints return data needed for weather rendering."""

    def test_farms_list_returns_200(self, client, db):
        _seed_farm(db)
        resp = client.get("/api/farms")
        assert resp.status_code == 200

    def test_farms_available_for_selector(self, client, db):
        _seed_farm(db)
        resp = client.get("/api/farms")
        data = resp.json()
        farms = data["data"]
        assert len(farms) >= 1
        assert farms[0]["name"] == "Rancho El Sol"
