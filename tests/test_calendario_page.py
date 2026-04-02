"""Tests for the crop calendar visualization page at /calendario."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

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


def _seed_calendario_data(db):
    """Seed farm with fields that have crop types and planting dates."""
    farm = Farm(name="Rancho Calendario", state="Jalisco", total_hectares=50.0)
    db.add(farm)
    db.flush()
    f1 = Field(
        farm_id=farm.id, name="Parcela Maiz", hectares=15.0,
        crop_type="maiz", planted_at=datetime(2026, 3, 1),
    )
    f2 = Field(
        farm_id=farm.id, name="Parcela Frijol", hectares=10.0,
        crop_type="frijol", planted_at=datetime(2026, 2, 15),
    )
    f3 = Field(
        farm_id=farm.id, name="Parcela Sin Cultivo", hectares=8.0,
        crop_type=None,
    )
    db.add_all([f1, f2, f3])
    db.commit()
    return farm, f1, f2, f3


class TestCalendarioPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/calendario")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/calendario")
        assert "Calendario" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/calendario")
        assert 'id="cal-farm-select"' in resp.text

    def test_page_has_field_selector(self, client):
        resp = client.get("/calendario")
        assert 'id="cal-field-select"' in resp.text

    def test_page_has_timeline_container(self, client):
        resp = client.get("/calendario")
        assert 'id="cal-timeline"' in resp.text

    def test_page_has_empty_state(self, client):
        resp = client.get("/calendario")
        assert 'id="cal-empty"' in resp.text

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/calendario")
        html = resp.text
        assert "Seleccione una granja" in html
        assert "Seleccione un campo" in html

    def test_page_has_js_script(self, client):
        resp = client.get("/calendario")
        assert "calendario.js" in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/calendario")
        assert "intel-nav" in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/calendario")
        html = resp.text
        assert 'id="cal-crop-count"' in html
        assert 'id="cal-total-days"' in html

    def test_page_has_stage_legend(self, client):
        resp = client.get("/calendario")
        html = resp.text
        assert "Siembra" in html
        assert "Vegetativo" in html
        assert "Cosecha" in html


class TestCalendarioPhenologyAPI:
    """API endpoint returns phenology calendar data for all crops."""

    def test_phenology_calendar_returns_200(self, client):
        resp = client.get("/api/phenology/calendar")
        assert resp.status_code == 200

    def test_phenology_calendar_returns_crops(self, client):
        resp = client.get("/api/phenology/calendar")
        data = resp.json()
        assert "crops" in data
        assert len(data["crops"]) >= 5

    def test_phenology_calendar_crop_has_stages(self, client):
        resp = client.get("/api/phenology/calendar")
        data = resp.json()
        crop = data["crops"][0]
        assert "crop_type" in crop
        assert "stages" in crop
        assert len(crop["stages"]) == 5

    def test_phenology_calendar_stage_has_day_ranges(self, client):
        resp = client.get("/api/phenology/calendar")
        data = resp.json()
        stage = data["crops"][0]["stages"][0]
        assert "name" in stage
        assert "name_es" in stage
        assert "start_day" in stage
        assert "end_day" in stage

    def test_phenology_calendar_maiz_present(self, client):
        resp = client.get("/api/phenology/calendar")
        data = resp.json()
        crop_types = [c["crop_type"] for c in data["crops"]]
        assert "maiz" in crop_types

    def test_farm_field_calendar_returns_growth_stage(self, client, db):
        farm, f1, f2, f3 = _seed_calendario_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{f1.id}/growth-stage")
        assert resp.status_code == 200
        data = resp.json()
        assert data["crop_type"] == "maiz"
        assert "all_stages" in data
        assert len(data["all_stages"]) == 5


class TestCalendarioPageContent:
    """Page HTML has correct structure for calendar rendering."""

    def test_page_has_calendario_link_in_nav(self, client):
        resp = client.get("/calendario")
        assert "/calendario" in resp.text

    def test_page_has_content_container(self, client):
        resp = client.get("/calendario")
        assert 'id="cal-content"' in resp.text

    def test_page_has_all_crops_section(self, client):
        resp = client.get("/calendario")
        assert 'id="cal-all-crops"' in resp.text

    def test_page_has_footer(self, client):
        resp = client.get("/calendario")
        assert "cultivos-footer" in resp.text
