"""Tests for the seasonal comparison page at /estaciones."""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord
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


def _make_health(field_id, score, ndvi_mean, scored_at):
    return HealthScore(
        field_id=field_id, score=score, ndvi_mean=ndvi_mean,
        scored_at=scored_at, sources=["ndvi"], breakdown={},
    )


def _make_treatment(field_id, desc, created_at):
    return TreatmentRecord(
        field_id=field_id, health_score_used=70.0,
        problema="Estrés", causa_probable="Sequía",
        tratamiento=desc, costo_estimado_mxn=500,
        urgencia="media", prevencion="Riego regular",
        organic=True, created_at=created_at,
    )


def _seed_seasonal_data(db):
    """Seed farm with field, health scores in both seasons, and treatments."""
    farm = Farm(name="Rancho Estaciones", state="Jalisco", total_hectares=50.0)
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Parcela Test", hectares=20.0, crop_type="maiz")
    db.add(field)
    db.flush()

    # Temporal season (Jun-Oct) health scores
    db.add(_make_health(field.id, 78.0, 0.72, datetime(2025, 7, 15)))
    db.add(_make_health(field.id, 82.0, 0.75, datetime(2025, 8, 10)))

    # Secas season (Nov-May) health scores
    db.add(_make_health(field.id, 60.0, 0.55, datetime(2025, 12, 5)))
    db.add(_make_health(field.id, 65.0, 0.58, datetime(2026, 2, 20)))

    # Treatments — one in temporal, two in secas
    db.add(_make_treatment(field.id, "Compost", datetime(2025, 7, 20)))
    db.add(_make_treatment(field.id, "Mulch", datetime(2025, 12, 10)))
    db.add(_make_treatment(field.id, "Vermicompost", datetime(2026, 1, 15)))

    db.commit()
    return farm, field


# ── Page Load Tests ────────────────────────────────────────────


class TestSeasonalPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/estaciones")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/estaciones")
        assert "Comparacion Estacional" in resp.text or "Estacional" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/estaciones")
        assert 'id="seasonal-farm-select"' in resp.text

    def test_page_has_field_selector(self, client):
        resp = client.get("/estaciones")
        assert 'id="seasonal-field-select"' in resp.text

    def test_page_has_season_cards_container(self, client):
        resp = client.get("/estaciones")
        assert 'id="seasonal-cards"' in resp.text

    def test_page_has_empty_state(self, client):
        resp = client.get("/estaciones")
        assert 'id="seasonal-empty"' in resp.text

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/estaciones")
        html = resp.text
        assert "Seleccione una granja" in html
        assert "Seleccione un campo" in html

    def test_page_has_js_script(self, client):
        resp = client.get("/estaciones")
        assert "seasonal.js" in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/estaciones")
        assert "intel-nav" in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/estaciones")
        html = resp.text
        assert 'id="seasonal-stat-temporal"' in html
        assert 'id="seasonal-stat-secas"' in html
        assert 'id="seasonal-stat-delta"' in html

    def test_page_has_comparison_table_container(self, client):
        resp = client.get("/estaciones")
        assert 'id="seasonal-comparison-table"' in resp.text

    def test_page_has_content_container(self, client):
        resp = client.get("/estaciones")
        assert 'id="seasonal-content"' in resp.text


# ── API Integration Tests ──────────────────────────────────────


class TestSeasonalAPI:
    """Seasonal comparison API returns expected data."""

    def test_seasonal_returns_seasons(self, client, db):
        farm, field = _seed_seasonal_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/seasonal-comparison")
        assert resp.status_code == 200
        data = resp.json()
        assert "temporal" in data
        assert "secas" in data

    def test_temporal_has_metrics(self, client, db):
        farm, field = _seed_seasonal_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/seasonal-comparison")
        data = resp.json()
        t = data["temporal"]
        assert "avg_health_score" in t
        assert "avg_ndvi" in t
        assert "treatment_count" in t
        assert "data_points" in t

    def test_temporal_values_correct(self, client, db):
        farm, field = _seed_seasonal_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/seasonal-comparison")
        data = resp.json()
        t = data["temporal"]
        assert t["avg_health_score"] == 80.0  # (78+82)/2
        assert t["treatment_count"] == 1
        assert t["data_points"] == 2

    def test_secas_values_correct(self, client, db):
        farm, field = _seed_seasonal_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/seasonal-comparison")
        data = resp.json()
        s = data["secas"]
        assert s["avg_health_score"] == 62.5  # (60+65)/2
        assert s["treatment_count"] == 2
        assert s["data_points"] == 2

    def test_available_years(self, client, db):
        farm, field = _seed_seasonal_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/seasonal-comparison")
        data = resp.json()
        assert "available_years" in data
        assert 2025 in data["available_years"]

    def test_year_filter(self, client, db):
        farm, field = _seed_seasonal_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/seasonal-comparison?year=2025")
        assert resp.status_code == 200
        data = resp.json()
        # 2025 temporal has 2 scores, 2025 secas has 1 score (Dec 2025)
        assert data["temporal"]["data_points"] == 2
        assert data["secas"]["data_points"] == 1

    def test_404_for_missing_farm(self, client, db):
        resp = client.get("/api/farms/9999/fields/1/seasonal-comparison")
        assert resp.status_code == 404

    def test_404_for_missing_field(self, client, db):
        farm = Farm(name="Solo", state="Jalisco", total_hectares=10.0)
        db.add(farm)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/9999/seasonal-comparison")
        assert resp.status_code == 404

    def test_empty_field_returns_nulls(self, client, db):
        farm = Farm(name="Vacia", state="Jalisco", total_hectares=10.0)
        db.add(farm)
        db.flush()
        field = Field(farm_id=farm.id, name="Sin Datos", hectares=5.0)
        db.add(field)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/seasonal-comparison")
        assert resp.status_code == 200
        data = resp.json()
        assert data["temporal"]["avg_health_score"] is None
        assert data["secas"]["avg_health_score"] is None


# ── Page Content Tests ─────────────────────────────────────────


class TestSeasonalPageContent:
    """Page HTML has correct structure for seasonal rendering."""

    def test_page_has_estaciones_link_in_nav(self, client):
        resp = client.get("/estaciones")
        assert "/estaciones" in resp.text

    def test_page_has_temporal_label(self, client):
        resp = client.get("/estaciones")
        assert "Temporal" in resp.text

    def test_page_has_secas_label(self, client):
        resp = client.get("/estaciones")
        assert "Secas" in resp.text

    def test_page_has_season_descriptions(self, client):
        resp = client.get("/estaciones")
        html = resp.text
        assert "Jun-Oct" in html
        assert "Nov-May" in html

    def test_page_has_delta_section(self, client):
        """Page should have a section for showing deltas between seasons."""
        resp = client.get("/estaciones")
        assert "seasonal-delta" in resp.text or "seasonal-comparison-table" in resp.text
