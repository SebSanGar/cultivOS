"""Tests for the drone fleet status page at /flota."""

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


# -- Page Load Tests --


class TestFlotaPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/flota")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/flota")
        assert "Flota de Drones" in resp.text

    def test_page_has_body_class(self, client):
        resp = client.get("/flota")
        assert 'class="intel-body"' in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/flota")
        assert "intel-nav" in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/flota")
        assert 'id="fleet-stats"' in resp.text

    def test_page_has_fleet_cards_container(self, client):
        resp = client.get("/flota")
        assert 'id="fleet-cards"' in resp.text


# -- Drone Card Tests --


class TestFlotaDroneCards:
    """Page contains cards for each drone in the fleet."""

    def test_has_mavic_multispectral(self, client):
        resp = client.get("/flota")
        assert "Mavic 3 Multispectral" in resp.text

    def test_has_mavic_thermal(self, client):
        resp = client.get("/flota")
        assert "Mavic 3 Thermal" in resp.text

    def test_has_agras_t100(self, client):
        resp = client.get("/flota")
        assert "Agras T100" in resp.text

    def test_has_battery_label(self, client):
        resp = client.get("/flota")
        assert "Bateria" in resp.text or "bateria" in resp.text

    def test_has_flight_hours_label(self, client):
        resp = client.get("/flota")
        assert "Horas de Vuelo" in resp.text or "horas de vuelo" in resp.text

    def test_has_maintenance_label(self, client):
        resp = client.get("/flota")
        assert "Mantenimiento" in resp.text or "mantenimiento" in resp.text

    def test_has_coverage_label(self, client):
        resp = client.get("/flota")
        assert "Cobertura" in resp.text or "cobertura" in resp.text

    def test_has_status_badges(self, client):
        resp = client.get("/flota")
        assert "status-badge" in resp.text

    def test_has_cost_info(self, client):
        resp = client.get("/flota")
        assert "MXN" in resp.text


# -- Stats Strip Tests --


class TestFlotaStatsStrip:
    """Stats strip shows fleet-level aggregates."""

    def test_has_total_drones_stat(self, client):
        resp = client.get("/flota")
        assert "Drones Totales" in resp.text or "drones-total" in resp.text

    def test_has_operational_stat(self, client):
        resp = client.get("/flota")
        assert "Operativos" in resp.text or "operativos" in resp.text

    def test_has_total_coverage_stat(self, client):
        resp = client.get("/flota")
        assert "Cobertura Total" in resp.text or "cobertura-total" in resp.text

    def test_has_investment_stat(self, client):
        resp = client.get("/flota")
        assert "Inversion" in resp.text or "inversion" in resp.text


# -- Navigation Tests --


class TestFlotaNavigation:
    """Page navigation links work correctly."""

    def test_nav_has_home_link(self, client):
        resp = client.get("/flota")
        assert 'href="/"' in resp.text

    def test_nav_has_mission_link(self, client):
        resp = client.get("/flota")
        assert 'href="/mision"' in resp.text

    def test_page_loads_js(self, client):
        resp = client.get("/flota")
        assert 'src="/flota.js"' in resp.text or "flota.js" in resp.text


# -- Content Quality Tests --


class TestFlotaContent:
    """Page has meaningful agricultural drone content."""

    def test_has_ndvi_mention(self, client):
        resp = client.get("/flota")
        assert "NDVI" in resp.text

    def test_has_thermal_mention(self, client):
        resp = client.get("/flota")
        assert "termic" in resp.text.lower() or "thermal" in resp.text.lower()

    def test_has_hectare_coverage(self, client):
        resp = client.get("/flota")
        assert "ha" in resp.text

    def test_has_spraying_mention(self, client):
        resp = client.get("/flota")
        assert "aspersion" in resp.text.lower() or "fumigacion" in resp.text.lower() or "aplicacion" in resp.text.lower()

    def test_has_lidar_mention(self, client):
        resp = client.get("/flota")
        assert "LiDAR" in resp.text

    def test_page_subtitle(self, client):
        resp = client.get("/flota")
        assert "intel-subtitle" in resp.text
