"""Tests for the yield prediction page at /rendimiento."""

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


def _seed_yield_data(db):
    """Seed farm with field and health score for yield prediction."""
    farm = Farm(name="Rancho Rendimiento", state="Jalisco", total_hectares=80.0)
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Parcela Maiz", hectares=25.0, crop_type="maiz")
    db.add(field)
    db.flush()
    hs = HealthScore(
        field_id=field.id, score=75.0, ndvi_mean=0.68,
        sources=["ndvi"], breakdown={},
    )
    db.add(hs)
    db.commit()
    return farm, field


# ── Page Load Tests ────────────────────────────────────────────


class TestYieldPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/rendimiento")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/rendimiento")
        assert "Prediccion de Rendimiento" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/rendimiento")
        assert 'id="yield-farm-select"' in resp.text

    def test_page_has_field_selector(self, client):
        resp = client.get("/rendimiento")
        assert 'id="yield-field-select"' in resp.text

    def test_page_has_yield_card_container(self, client):
        resp = client.get("/rendimiento")
        assert 'id="yield-card"' in resp.text

    def test_page_has_empty_state(self, client):
        resp = client.get("/rendimiento")
        assert 'id="yield-empty"' in resp.text

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/rendimiento")
        html = resp.text
        assert "Seleccione una granja" in html
        assert "Seleccione un campo" in html

    def test_page_has_js_script(self, client):
        resp = client.get("/rendimiento")
        assert "yield.js" in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/rendimiento")
        assert "intel-nav" in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/rendimiento")
        html = resp.text
        assert 'id="yield-stat-estimate"' in html
        assert 'id="yield-stat-range"' in html
        assert 'id="yield-stat-total"' in html

    def test_page_has_factors_section(self, client):
        resp = client.get("/rendimiento")
        assert 'id="yield-factors"' in resp.text

    def test_page_has_confidence_section(self, client):
        resp = client.get("/rendimiento")
        assert 'id="yield-confidence"' in resp.text


# ── API Integration Tests ──────────────────────────────────────


class TestYieldAPI:
    """Yield API returns expected data through the page's API."""

    def test_yield_returns_prediction(self, client, db):
        farm, field = _seed_yield_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/yield")
        assert resp.status_code == 200
        data = resp.json()
        assert "kg_per_ha" in data
        assert "min_kg_per_ha" in data
        assert "max_kg_per_ha" in data
        assert "total_kg" in data
        assert "nota" in data

    def test_yield_values_reasonable(self, client, db):
        farm, field = _seed_yield_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/yield")
        data = resp.json()
        assert data["crop_type"] == "maiz"
        assert data["hectares"] == 25.0
        assert data["kg_per_ha"] > 0
        assert data["min_kg_per_ha"] < data["kg_per_ha"]
        assert data["max_kg_per_ha"] > data["kg_per_ha"]
        assert data["total_kg"] == pytest.approx(data["kg_per_ha"] * 25.0, rel=0.01)

    def test_404_for_missing_farm(self, client, db):
        resp = client.get("/api/farms/9999/fields/1/yield")
        assert resp.status_code == 404

    def test_404_for_missing_field(self, client, db):
        farm = Farm(name="Solo", state="Jalisco", total_hectares=10.0)
        db.add(farm)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/9999/yield")
        assert resp.status_code == 404

    def test_yield_without_health_data(self, client, db):
        """Field with no health scores should still return prediction with default."""
        farm = Farm(name="Vacia", state="Jalisco", total_hectares=10.0)
        db.add(farm)
        db.flush()
        field = Field(farm_id=farm.id, name="Sin Datos", hectares=5.0, crop_type="frijol")
        db.add(field)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/yield")
        assert resp.status_code == 200
        data = resp.json()
        assert data["kg_per_ha"] > 0
        assert "insuficientes" in data["nota"].lower() or "basada en promedio" in data["nota"].lower()


# ── Page Content Tests ─────────────────────────────────────────


class TestYieldPageContent:
    """Page HTML has correct structure for yield rendering."""

    def test_page_has_rendimiento_link_in_nav(self, client):
        resp = client.get("/rendimiento")
        assert "/rendimiento" in resp.text

    def test_page_has_crop_type_label(self, client):
        resp = client.get("/rendimiento")
        assert "Estimacion" in resp.text or "cosecha" in resp.text.lower()

    def test_page_has_uncertainty_label(self, client):
        resp = client.get("/rendimiento")
        html = resp.text
        assert "Rango" in html or "Incertidumbre" in html or "min" in html.lower()

    def test_page_has_nota_section(self, client):
        resp = client.get("/rendimiento")
        assert 'id="yield-nota"' in resp.text
