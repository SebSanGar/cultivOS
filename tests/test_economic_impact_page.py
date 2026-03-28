"""Tests for the farm economic impact report page at /impacto-economico."""

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Farm, Field, HealthScore
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
    """Seed a farm with fields and health scores for economic impact testing."""
    farm = Farm(name="Rancho Prueba", state="Jalisco", total_hectares=20.0)
    db.add(farm)
    db.flush()
    f1 = Field(farm_id=farm.id, name="Maiz Norte", hectares=12.0, crop_type="maiz")
    f2 = Field(farm_id=farm.id, name="Agave Sur", hectares=8.0, crop_type="agave")
    db.add_all([f1, f2])
    db.flush()
    # Add health scores
    from datetime import datetime
    hs1 = HealthScore(field_id=f1.id, score=72.0, scored_at=datetime(2026, 3, 1))
    hs2 = HealthScore(field_id=f2.id, score=65.0, scored_at=datetime(2026, 3, 1))
    db.add_all([hs1, hs2])
    db.commit()
    return farm


class TestEconomicImpactPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/impacto-economico")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/impacto-economico")
        assert "Impacto Econ" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/impacto-economico")
        assert 'id="econ-farm-select"' in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/impacto-economico")
        html = resp.text
        assert 'id="econ-total-savings"' in html
        assert 'id="econ-hectares"' in html
        assert 'id="econ-water"' in html
        assert 'id="econ-fertilizer"' in html

    def test_page_has_chart_container(self, client):
        resp = client.get("/impacto-economico")
        assert 'id="econ-chart"' in resp.text

    def test_page_has_savings_cards(self, client):
        resp = client.get("/impacto-economico")
        assert 'id="econ-cards"' in resp.text

    def test_page_shows_mxn_currency(self, client):
        resp = client.get("/impacto-economico")
        assert "MXN" in resp.text

    def test_page_has_nota_container(self, client):
        resp = client.get("/impacto-economico")
        assert 'id="econ-nota"' in resp.text


class TestEconomicImpactPageContent:
    """Page content and Spanish labels."""

    def test_page_has_water_label(self, client):
        resp = client.get("/impacto-economico")
        assert "Ahorro en agua" in resp.text or "Agua" in resp.text

    def test_page_has_fertilizer_label(self, client):
        resp = client.get("/impacto-economico")
        assert "Fertilizante" in resp.text

    def test_page_has_yield_label(self, client):
        resp = client.get("/impacto-economico")
        assert "Rendimiento" in resp.text

    def test_page_has_nav_link(self, client):
        resp = client.get("/impacto-economico")
        assert '/impacto-economico' in resp.text

    def test_page_loads_js(self, client):
        resp = client.get("/impacto-economico")
        assert "economic-impact.js" in resp.text

    def test_page_loads_chart_js(self, client):
        resp = client.get("/impacto-economico")
        assert "chart" in resp.text.lower() or "Chart" in resp.text


class TestEconomicImpactAPI:
    """API integration sanity checks via the page."""

    def test_farm_economic_endpoint_returns_data(self, client, db):
        farm = _seed_farm(db)
        resp = client.get(f"/api/farms/{farm.id}/economic-impact")
        assert resp.status_code == 200
        data = resp.json()
        assert data["farm_id"] == farm.id
        assert data["hectares"] == 20.0
        assert data["total_savings_mxn"] > 0
        assert data["water_savings_mxn"] > 0
        assert data["fertilizer_savings_mxn"] >= 0
        assert data["yield_improvement_mxn"] > 0
        assert "MXN" in data["nota"] or "economico" in data["nota"].lower()

    def test_farm_economic_empty_farm(self, client, db):
        farm = Farm(name="Vacia", state="Jalisco", total_hectares=0.0)
        db.add(farm)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/economic-impact")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_savings_mxn"] == 0
