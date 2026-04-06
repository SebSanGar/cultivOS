"""Tests for the crop rotation planner page at /rotacion."""

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Farm, Field, SoilAnalysis
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


def _seed_rotation_data(db):
    """Seed farm with field that has crop_type and soil data for rotation planning."""
    farm = Farm(name="Rancho Rotacion", state="Jalisco", total_hectares=40.0)
    db.add(farm)
    db.flush()
    f1 = Field(farm_id=farm.id, name="Parcela Maiz", hectares=15.0, crop_type="maiz")
    f2 = Field(farm_id=farm.id, name="Parcela Vacia", hectares=10.0, crop_type=None)
    db.add_all([f1, f2])
    db.flush()
    # Soil analysis for f1 — low nitrogen triggers legume rotation
    db.add(SoilAnalysis(
        field_id=f1.id, ph=6.0, organic_matter_pct=1.8,
        nitrogen_ppm=8.0, phosphorus_ppm=15.0, potassium_ppm=140.0,
        texture="franco", moisture_pct=20.0, sampled_at=datetime(2026, 1, 15),
    ))
    db.commit()
    return farm, f1, f2


class TestRotationPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/rotacion")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/rotacion")
        assert "Rotacion" in resp.text or "Rotaci" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/rotacion")
        assert 'id="rotation-farm-select"' in resp.text

    def test_page_has_field_selector(self, client):
        resp = client.get("/rotacion")
        assert 'id="rotation-field-select"' in resp.text

    def test_page_has_season_cards_container(self, client):
        resp = client.get("/rotacion")
        assert 'id="rotation-cards"' in resp.text

    def test_page_has_empty_state(self, client):
        resp = client.get("/rotacion")
        assert 'id="rotation-empty"' in resp.text

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/rotacion")
        html = resp.text
        assert "Seleccione una granja" in html
        assert "Seleccione un campo" in html

    def test_page_has_js_script(self, client):
        resp = client.get("/rotacion")
        assert "rotation.js" in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/rotacion")
        assert "intel-nav" in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/rotacion")
        html = resp.text
        assert 'id="rotation-last-crop"' in html
        assert 'id="rotation-region"' in html
        assert 'id="rotation-seasons"' in html


class TestRotationAPI:
    """Rotation API returns expected plan data."""

    def test_rotation_returns_plan(self, client, db):
        farm, f1, f2 = _seed_rotation_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{f1.id}/rotation")
        assert resp.status_code == 200
        data = resp.json()
        assert "plan" in data
        assert "last_crop" in data
        assert "region" in data
        assert len(data["plan"]) >= 3

    def test_rotation_plan_has_season_fields(self, client, db):
        farm, f1, f2 = _seed_rotation_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{f1.id}/rotation")
        data = resp.json()
        entry = data["plan"][0]
        assert "season" in entry
        assert "crop" in entry
        assert "reason" in entry
        assert "purpose" in entry
        assert "months" in entry

    def test_rotation_422_for_no_crop_type(self, client, db):
        farm, f1, f2 = _seed_rotation_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{f2.id}/rotation")
        assert resp.status_code == 422

    def test_rotation_404_for_missing_farm(self, client, db):
        resp = client.get("/api/farms/9999/fields/1/rotation")
        assert resp.status_code == 404

    def test_rotation_after_maiz_suggests_legume(self, client, db):
        """After maiz (heavy feeder) with low nitrogen, rotation should include legume."""
        farm, f1, f2 = _seed_rotation_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{f1.id}/rotation")
        data = resp.json()
        crops = [e["crop"] for e in data["plan"]]
        # Should include a legume (frijol, veza, etc.) for nitrogen fixation
        legumes = {"frijol", "lenteja", "haba", "veza", "garbanzo"}
        assert any(c in legumes for c in crops), f"Expected legume in rotation, got {crops}"


class TestRotationPageContent:
    """Page HTML has correct structure for rotation rendering."""

    def test_page_has_rotacion_link_in_nav(self, client):
        resp = client.get("/rotacion")
        assert "/rotacion" in resp.text

    def test_page_has_season_labels(self, client):
        resp = client.get("/rotacion")
        html = resp.text
        # Page should reference seasons in Spanish
        assert "Temporada" in html or "temporada" in html or "Estacion" in html or "Plan de Rotacion" in html

    def test_page_has_content_container(self, client):
        resp = client.get("/rotacion")
        assert 'id="rotation-content"' in resp.text


class TestMultiYearPageElements:
    """Page HTML has multi-year plan section."""

    def test_page_has_multiyear_section(self, client):
        resp = client.get("/rotacion")
        assert 'id="multiyear-section"' in resp.text

    def test_page_has_milpa_badge(self, client):
        resp = client.get("/rotacion")
        assert 'id="milpa-badge"' in resp.text

    def test_page_has_milpa_description(self, client):
        resp = client.get("/rotacion")
        assert 'id="milpa-description"' in resp.text

    def test_page_has_milpa_info_container(self, client):
        resp = client.get("/rotacion")
        assert 'id="milpa-info"' in resp.text

    def test_page_has_om_start_stat(self, client):
        resp = client.get("/rotacion")
        assert 'id="om-start-val"' in resp.text

    def test_page_has_om_end_stat(self, client):
        resp = client.get("/rotacion")
        assert 'id="om-end-val"' in resp.text

    def test_page_has_om_delta_stat(self, client):
        resp = client.get("/rotacion")
        assert 'id="om-delta-val"' in resp.text

    def test_page_has_om_chart_canvas(self, client):
        resp = client.get("/rotacion")
        assert 'id="om-chart"' in resp.text

    def test_page_has_multiyear_cards_container(self, client):
        resp = client.get("/rotacion")
        assert 'id="multiyear-cards"' in resp.text

    def test_page_has_3_year_title(self, client):
        resp = client.get("/rotacion")
        assert "3 Anos" in resp.text or "3 anos" in resp.text

    def test_page_has_mo_labels(self, client):
        resp = client.get("/rotacion")
        html = resp.text
        assert "MO Inicial" in html
        assert "MO Final" in html
        assert "Cambio MO" in html

    def test_page_has_milpa_badge_text(self, client):
        resp = client.get("/rotacion")
        assert "Sistema Milpa" in resp.text

    def test_multiyear_api_returns_plan(self, client, db):
        """Multi-year endpoint returns valid plan data."""
        farm, f1, f2 = _seed_rotation_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{f1.id}/rotation/multi-year")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["plan"]) == 6
        assert data["total_years"] == 3
        assert "milpa_recommended" in data
        assert "om_start" in data
        assert "om_end" in data

    def test_multiyear_entries_have_year_and_om(self, client, db):
        farm, f1, f2 = _seed_rotation_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{f1.id}/rotation/multi-year")
        data = resp.json()
        for entry in data["plan"]:
            assert "year" in entry
            assert "organic_matter_pct" in entry
            assert "season" in entry
            assert "crop" in entry

    def test_multiyear_milpa_for_maiz_field(self, client, db):
        farm, f1, f2 = _seed_rotation_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{f1.id}/rotation/multi-year")
        data = resp.json()
        assert data["milpa_recommended"] is True
        assert "milpa" in data["milpa_description"].lower()
