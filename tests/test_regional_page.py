"""Tests for the regional intelligence page at /regional."""

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Farm, Field
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


def _seed_regional_data(db):
    """Seed two farms in different states for regional view."""
    farm1 = Farm(name="Rancho Jalisco", state="Jalisco", total_hectares=80.0)
    farm2 = Farm(name="Rancho Michoacan", state="Michoacan", total_hectares=50.0)
    db.add_all([farm1, farm2])
    db.flush()
    f1 = Field(farm_id=farm1.id, name="Parcela A", hectares=40.0, crop_type="maiz")
    f2 = Field(farm_id=farm1.id, name="Parcela B", hectares=40.0, crop_type="aguacate")
    f3 = Field(farm_id=farm2.id, name="Parcela C", hectares=50.0, crop_type="agave")
    db.add_all([f1, f2, f3])
    db.commit()
    return farm1, farm2


# ── Page Load Tests ────────────────────────────────────────────


class TestRegionalPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/regional")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/regional")
        assert "Inteligencia Regional" in resp.text

    def test_page_has_state_filter(self, client):
        resp = client.get("/regional")
        assert 'id="regional-state-filter"' in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/regional")
        assert 'id="regional-stat-regions"' in resp.text
        assert 'id="regional-stat-farms"' in resp.text
        assert 'id="regional-stat-fields"' in resp.text
        assert 'id="regional-stat-hectares"' in resp.text

    def test_page_has_regions_container(self, client):
        resp = client.get("/regional")
        assert 'id="regional-regions"' in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/regional")
        assert "intel-nav" in resp.text

    def test_page_has_script(self, client):
        resp = client.get("/regional")
        assert "regional.js" in resp.text


# ── DOM Elements Tests ─────────────────────────────────────────


class TestRegionalDOMElements:
    """Key DOM elements exist for JS rendering."""

    def test_crop_distribution_container(self, client):
        resp = client.get("/regional")
        assert "crop-distribution" in resp.text or "regional-regions" in resp.text

    def test_treatment_section_exists(self, client):
        resp = client.get("/regional")
        assert "Tratamientos" in resp.text or "tratamiento" in resp.text.lower()

    def test_empty_state_message(self, client):
        resp = client.get("/regional")
        assert 'id="regional-empty"' in resp.text


# ── API Integration Tests ──────────────────────────────────────


class TestRegionalAPI:
    """API endpoint returns regional data."""

    def test_regional_summary_returns_200(self, client, db):
        _seed_regional_data(db)
        resp = client.get("/api/intel/regional-summary")
        assert resp.status_code == 200

    def test_regional_summary_has_regions(self, client, db):
        _seed_regional_data(db)
        resp = client.get("/api/intel/regional-summary")
        data = resp.json()
        assert "regions" in data
        assert len(data["regions"]) >= 2

    def test_regional_summary_state_filter(self, client, db):
        _seed_regional_data(db)
        resp = client.get("/api/intel/regional-summary?state=Jalisco")
        data = resp.json()
        assert len(data["regions"]) == 1
        assert data["regions"][0]["state"] == "Jalisco"

    def test_regional_summary_has_crop_distribution(self, client, db):
        _seed_regional_data(db)
        resp = client.get("/api/intel/regional-summary?state=Jalisco")
        data = resp.json()
        region = data["regions"][0]
        assert "crop_distribution" in region
        assert len(region["crop_distribution"]) >= 1
