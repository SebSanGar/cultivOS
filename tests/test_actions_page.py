"""Tests for the unified action timeline page at /acciones."""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Farm, Field, TreatmentRecord, WeatherRecord
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


def _seed_actions_data(db):
    """Seed farm, field, pending treatment, and weather for action timeline."""
    farm = Farm(name="Rancho Acciones", state="Jalisco", total_hectares=60.0)
    db.add(farm)
    db.flush()
    field = Field(
        farm_id=farm.id, name="Parcela Norte", hectares=20.0,
        crop_type="maiz", planted_at=datetime(2026, 3, 1),
    )
    db.add(field)
    db.flush()
    # Pending treatment (applied_at is None)
    treatment = TreatmentRecord(
        field_id=field.id, health_score_used=65.0,
        problema="Deficiencia de nitrogeno",
        causa_probable="Suelo agotado",
        tratamiento="Aplicar composta organica 5 ton/ha",
        costo_estimado_mxn=3500, urgencia="alta",
        prevencion="Rotacion con leguminosas", organic=True,
    )
    db.add(treatment)
    # Weather record with forecast
    weather = WeatherRecord(
        farm_id=farm.id, temp_c=28.0, humidity_pct=65.0,
        wind_kmh=12.0, rainfall_mm=0.0, description="Parcialmente nublado",
        forecast_3day=[
            {"temp_c": 30.0, "rainfall_mm": 0.0},
            {"temp_c": 28.0, "rainfall_mm": 12.0},
            {"temp_c": 27.0, "rainfall_mm": 0.0},
        ],
    )
    db.add(weather)
    db.commit()
    return farm, field


# ── Page Load Tests ────────────────────────────────────────────


class TestActionsPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/acciones")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/acciones")
        assert "Linea de Acciones" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/acciones")
        assert 'id="actions-farm-select"' in resp.text

    def test_page_has_field_selector(self, client):
        resp = client.get("/acciones")
        assert 'id="actions-field-select"' in resp.text

    def test_page_has_actions_container(self, client):
        resp = client.get("/acciones")
        assert 'id="actions-list"' in resp.text

    def test_page_has_empty_state(self, client):
        resp = client.get("/acciones")
        assert 'id="actions-empty"' in resp.text

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/acciones")
        html = resp.text
        assert "Seleccione una granja" in html
        assert "Seleccione un campo" in html

    def test_page_has_js_script(self, client):
        resp = client.get("/acciones")
        assert "actions.js" in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/acciones")
        assert "intel-nav" in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/acciones")
        html = resp.text
        assert 'id="actions-stat-total"' in html
        assert 'id="actions-stat-priority"' in html
        assert 'id="actions-stat-weather"' in html

    def test_page_has_weather_summary_section(self, client):
        resp = client.get("/acciones")
        assert 'id="actions-weather"' in resp.text


# ── API Integration Tests ──────────────────────────────────────


class TestActionsAPI:
    """Action timeline API returns expected data."""

    def test_timeline_returns_actions(self, client, db):
        farm, field = _seed_actions_data(db)
        resp = client.get(
            f"/api/farms/{farm.id}/fields/{field.id}/action-timeline"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "actions" in data
        assert "action_count" in data
        assert data["action_count"] >= 1

    def test_timeline_has_treatment_action(self, client, db):
        farm, field = _seed_actions_data(db)
        resp = client.get(
            f"/api/farms/{farm.id}/fields/{field.id}/action-timeline"
        )
        data = resp.json()
        treatments = [a for a in data["actions"] if a["source"] == "treatment"]
        assert len(treatments) >= 1
        assert treatments[0]["urgencia"] == "alta"
        assert treatments[0]["action_type"] == "tratamiento"

    def test_timeline_has_weather_summary(self, client, db):
        farm, field = _seed_actions_data(db)
        resp = client.get(
            f"/api/farms/{farm.id}/fields/{field.id}/action-timeline"
        )
        data = resp.json()
        ws = data["weather_summary"]
        assert ws is not None
        assert "total_rainfall_mm" in ws
        assert ws["rainy_days"] == 1

    def test_timeline_sorted_by_priority(self, client, db):
        farm, field = _seed_actions_data(db)
        resp = client.get(
            f"/api/farms/{farm.id}/fields/{field.id}/action-timeline"
        )
        data = resp.json()
        priorities = [a["priority"] for a in data["actions"]]
        assert priorities == sorted(priorities)

    def test_404_for_missing_farm(self, client, db):
        resp = client.get("/api/farms/9999/fields/1/action-timeline")
        assert resp.status_code == 404

    def test_404_for_missing_field(self, client, db):
        farm = Farm(name="Solo", state="Jalisco", total_hectares=10.0)
        db.add(farm)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/9999/action-timeline")
        assert resp.status_code == 404

    def test_timeline_without_weather(self, client, db):
        """Field with no weather should still return actions."""
        farm = Farm(name="Seca", state="Jalisco", total_hectares=10.0)
        db.add(farm)
        db.flush()
        field = Field(
            farm_id=farm.id, name="Sin Clima", hectares=5.0,
            crop_type="maiz", planted_at=datetime(2026, 3, 1),
        )
        db.add(field)
        db.commit()
        resp = client.get(
            f"/api/farms/{farm.id}/fields/{field.id}/action-timeline"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["weather_summary"] is None

    def test_reference_date_param(self, client, db):
        farm, field = _seed_actions_data(db)
        resp = client.get(
            f"/api/farms/{farm.id}/fields/{field.id}/action-timeline",
            params={"reference_date": "2026-07-15"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["reference_date"] == "2026-07-15"


# ── Page Content Tests ─────────────────────────────────────────


class TestActionsPageContent:
    """Page HTML has correct structure for action rendering."""

    def test_page_has_acciones_link_in_nav(self, client):
        resp = client.get("/acciones")
        assert "/acciones" in resp.text

    def test_page_has_action_type_labels(self, client):
        resp = client.get("/acciones")
        html = resp.text
        # Priority badge text should exist in the template or JS
        assert "Prioridad" in html or "prioridad" in html.lower()

    def test_page_has_date_display(self, client):
        resp = client.get("/acciones")
        assert 'id="actions-date"' in resp.text
