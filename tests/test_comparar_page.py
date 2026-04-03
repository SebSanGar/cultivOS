"""Tests for the farm comparison page at /comparar."""

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


def _seed_comparison_data(db):
    """Seed multiple farms for comparison testing."""
    farm1 = Farm(
        name="Rancho El Sol", state="Jalisco", total_hectares=100.0,
        location_lat=20.6597, location_lon=-103.3496, municipality="Zapopan"
    )
    farm2 = Farm(
        name="Rancho La Luna", state="Jalisco", total_hectares=60.0,
        location_lat=20.7200, location_lon=-103.4000, municipality="Tlajomulco"
    )
    farm3 = Farm(
        name="Rancho El Cielo", state="Jalisco", total_hectares=80.0,
        location_lat=20.6800, location_lon=-103.3700, municipality="Tonala"
    )
    db.add_all([farm1, farm2, farm3])
    db.flush()
    f1 = Field(farm_id=farm1.id, name="Parcela Norte", hectares=50.0, crop_type="maiz")
    f2 = Field(farm_id=farm2.id, name="Parcela Central", hectares=60.0, crop_type="agave")
    db.add_all([f1, f2])
    db.flush()
    hs1 = HealthScore(field_id=f1.id, score=82.0, scored_at=datetime(2026, 3, 1))
    hs2 = HealthScore(field_id=f2.id, score=55.0, scored_at=datetime(2026, 3, 1))
    db.add_all([hs1, hs2])
    db.commit()
    return farm1, farm2, farm3


# -- Page Load Tests --


class TestCompararPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/comparar")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/comparar")
        assert "Comparar Granjas" in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/comparar")
        assert "intel-nav" in resp.text

    def test_page_has_script(self, client):
        resp = client.get("/comparar")
        assert "comparar.js" in resp.text

    def test_page_has_footer(self, client):
        resp = client.get("/comparar")
        assert "cultivos-footer" in resp.text

    def test_page_has_subtitle(self, client):
        resp = client.get("/comparar")
        assert "2-3 granjas" in resp.text


# -- DOM Elements Tests --


class TestCompararDOMElements:
    """Key DOM elements exist for JS comparison rendering."""

    def test_farm_selectors_exist(self, client):
        resp = client.get("/comparar")
        assert 'id="comp-farm-1"' in resp.text
        assert 'id="comp-farm-2"' in resp.text
        assert 'id="comp-farm-3"' in resp.text

    def test_compare_button_exists(self, client):
        resp = client.get("/comparar")
        assert 'id="comp-btn"' in resp.text

    def test_comparison_results_container(self, client):
        resp = client.get("/comparar")
        assert 'id="comp-results"' in resp.text

    def test_comparison_table_exists(self, client):
        resp = client.get("/comparar")
        assert 'id="comp-table"' in resp.text

    def test_health_chart_canvas(self, client):
        resp = client.get("/comparar")
        assert 'id="comp-health-chart"' in resp.text

    def test_yield_chart_canvas(self, client):
        resp = client.get("/comparar")
        assert 'id="comp-yield-chart"' in resp.text

    def test_history_chart_canvas(self, client):
        resp = client.get("/comparar")
        assert 'id="comp-history-chart"' in resp.text

    def test_empty_state_exists(self, client):
        resp = client.get("/comparar")
        assert 'id="comp-empty"' in resp.text

    def test_spanish_labels(self, client):
        resp = client.get("/comparar")
        text = resp.text
        assert "Resumen Comparativo" in text
        assert "Salud Promedio" in text
        assert "Rendimiento" in text
        assert "Historial de Salud" in text

    def test_farm_3_is_optional(self, client):
        resp = client.get("/comparar")
        assert "opcional" in resp.text.lower()


# -- API Integration Tests --


class TestCompararAPIIntegration:
    """API endpoints return data needed for farm comparison."""

    def test_farms_list_returns_200(self, client, db):
        _seed_comparison_data(db)
        resp = client.get("/api/farms")
        assert resp.status_code == 200

    def test_multiple_farms_available(self, client, db):
        _seed_comparison_data(db)
        resp = client.get("/api/farms")
        data = resp.json()
        farms = data["data"]
        assert len(farms) >= 3

    def test_farm_fields_available(self, client, db):
        farm1, _, _ = _seed_comparison_data(db)
        resp = client.get(f"/api/farms/{farm1.id}/fields")
        assert resp.status_code == 200
        fields = resp.json()
        assert len(fields) >= 1
