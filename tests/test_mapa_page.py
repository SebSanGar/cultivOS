"""Tests for the interactive field map page at /mapa."""

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Farm, Field, HealthScore
from cultivos.db.session import get_db
from datetime import datetime


@pytest.fixture()
def app(db):
    application = create_app()
    application.dependency_overrides[get_db] = lambda: db
    yield application
    application.dependency_overrides.clear()


@pytest.fixture()
def client(app):
    return TestClient(app, raise_server_exceptions=False)


def _seed_map_data(db):
    """Seed farms with GPS coordinates and fields with boundaries and health scores."""
    farm1 = Farm(
        name="Rancho El Sol", state="Jalisco", total_hectares=100.0,
        location_lat=20.6597, location_lon=-103.3496, municipality="Zapopan"
    )
    farm2 = Farm(
        name="Rancho La Luna", state="Jalisco", total_hectares=60.0,
        location_lat=20.7200, location_lon=-103.4000, municipality="Tlajomulco"
    )
    db.add_all([farm1, farm2])
    db.flush()
    f1 = Field(
        farm_id=farm1.id, name="Parcela Norte", hectares=50.0, crop_type="maiz",
        boundary_coordinates=[[-103.35, 20.66], [-103.34, 20.66], [-103.34, 20.65], [-103.35, 20.65]]
    )
    f2 = Field(
        farm_id=farm1.id, name="Parcela Sur", hectares=50.0, crop_type="agave",
        boundary_coordinates=[[-103.36, 20.65], [-103.35, 20.65], [-103.35, 20.64], [-103.36, 20.64]]
    )
    f3 = Field(
        farm_id=farm2.id, name="Parcela Central", hectares=60.0, crop_type="aguacate"
    )
    db.add_all([f1, f2, f3])
    db.flush()
    # Health scores for color coding
    hs1 = HealthScore(field_id=f1.id, score=82.0, scored_at=datetime(2026, 3, 1))
    hs2 = HealthScore(field_id=f2.id, score=45.0, scored_at=datetime(2026, 3, 1))
    hs3 = HealthScore(field_id=f3.id, score=25.0, scored_at=datetime(2026, 3, 1))
    db.add_all([hs1, hs2, hs3])
    db.commit()
    return farm1, farm2


# -- Page Load Tests --


class TestMapaPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/mapa")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/mapa")
        assert "Mapa de Campos" in resp.text

    def test_page_has_map_container(self, client):
        resp = client.get("/mapa")
        assert 'id="map-container"' in resp.text

    def test_page_has_legend(self, client):
        resp = client.get("/mapa")
        assert 'id="map-legend"' in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/mapa")
        assert 'id="map-farm-filter"' in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/mapa")
        assert "intel-nav" in resp.text

    def test_page_has_script(self, client):
        resp = client.get("/mapa")
        assert "mapa.js" in resp.text

    def test_page_has_leaflet_css(self, client):
        resp = client.get("/mapa")
        assert "leaflet" in resp.text.lower()

    def test_page_has_leaflet_js(self, client):
        resp = client.get("/mapa")
        assert "leaflet" in resp.text.lower()


# -- DOM Elements Tests --


class TestMapaDOMElements:
    """Key DOM elements exist for JS map rendering."""

    def test_stats_strip_exists(self, client):
        resp = client.get("/mapa")
        assert 'id="map-stat-farms"' in resp.text
        assert 'id="map-stat-fields"' in resp.text
        assert 'id="map-stat-hectares"' in resp.text

    def test_health_color_legend(self, client):
        resp = client.get("/mapa")
        text = resp.text.lower()
        assert "bueno" in text or "saludable" in text
        assert "alerta" in text or "moderado" in text

    def test_empty_state_message(self, client):
        resp = client.get("/mapa")
        assert 'id="map-empty"' in resp.text

    def test_info_panel_exists(self, client):
        resp = client.get("/mapa")
        assert 'id="map-info-panel"' in resp.text


# -- API Integration Tests --


class TestMapaAPIIntegration:
    """API endpoints return data needed for map rendering."""

    def test_farms_list_returns_200(self, client, db):
        _seed_map_data(db)
        resp = client.get("/api/farms")
        assert resp.status_code == 200

    def test_farms_have_coordinates(self, client, db):
        _seed_map_data(db)
        resp = client.get("/api/farms")
        data = resp.json()
        farms = data["data"]
        assert len(farms) >= 2
        has_coords = any(f.get("location_lat") is not None for f in farms)
        assert has_coords

    def test_fields_have_boundaries(self, client, db):
        farm1, _ = _seed_map_data(db)
        resp = client.get(f"/api/farms/{farm1.id}/fields")
        fields = resp.json()
        has_boundary = any(f.get("boundary_coordinates") is not None for f in fields)
        assert has_boundary

    def test_fields_list_returns_200(self, client, db):
        farm1, _ = _seed_map_data(db)
        resp = client.get(f"/api/farms/{farm1.id}/fields")
        assert resp.status_code == 200
        fields = resp.json()
        assert len(fields) >= 2
