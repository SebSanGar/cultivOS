"""Tests for the drone mission planner page at /mision."""

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


def _seed_mission_data(db):
    """Seed farm with fields — one with boundary coords, one without."""
    farm = Farm(name="Rancho Mision", state="Jalisco", total_hectares=50.0)
    db.add(farm)
    db.flush()
    f_with_boundary = Field(
        farm_id=farm.id, name="Parcela Norte", hectares=20.0, crop_type="maiz",
        boundary_coordinates=[
            [-103.3496, 20.6597],
            [-103.3446, 20.6597],
            [-103.3446, 20.6547],
            [-103.3496, 20.6547],
        ],
    )
    f_no_boundary = Field(
        farm_id=farm.id, name="Parcela Sin Limites", hectares=10.0, crop_type="frijol",
    )
    db.add_all([f_with_boundary, f_no_boundary])
    db.commit()
    return farm, f_with_boundary, f_no_boundary


class TestMissionPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/mision")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/mision")
        assert "Mision" in resp.text or "mision" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/mision")
        assert 'id="mission-farm-select"' in resp.text

    def test_page_has_field_selector(self, client):
        resp = client.get("/mision")
        assert 'id="mission-field-select"' in resp.text

    def test_page_has_mission_type_dropdown(self, client):
        resp = client.get("/mision")
        assert 'id="mission-type-select"' in resp.text

    def test_page_has_drone_type_dropdown(self, client):
        resp = client.get("/mision")
        assert 'id="mission-drone-select"' in resp.text

    def test_page_has_generate_button(self, client):
        resp = client.get("/mision")
        assert "Generar" in resp.text

    def test_page_has_results_container(self, client):
        resp = client.get("/mision")
        assert 'id="mission-results"' in resp.text

    def test_page_has_empty_state(self, client):
        resp = client.get("/mision")
        assert 'id="mission-empty"' in resp.text

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/mision")
        html = resp.text
        assert "Seleccione una granja" in html
        assert "Seleccione un campo" in html

    def test_page_has_js_script(self, client):
        resp = client.get("/mision")
        assert "mission.js" in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/mision")
        assert "intel-nav" in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/mision")
        html = resp.text
        assert 'id="mission-duration"' in html
        assert 'id="mission-area"' in html
        assert 'id="mission-batteries"' in html


class TestMissionAPI:
    """Mission plan API returns expected data."""

    def test_mission_plan_returns_200(self, client, db):
        farm, f_with, f_no = _seed_mission_data(db)
        resp = client.get(
            f"/api/farms/{farm.id}/fields/{f_with.id}/mission-plan",
            params={"mission_type": "health_scan", "drone_type": "mavic_multispectral"},
        )
        assert resp.status_code == 200

    def test_mission_plan_has_waypoints(self, client, db):
        farm, f_with, f_no = _seed_mission_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{f_with.id}/mission-plan")
        data = resp.json()
        assert "waypoints" in data
        assert len(data["waypoints"]) > 0

    def test_mission_plan_has_flight_params(self, client, db):
        farm, f_with, f_no = _seed_mission_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{f_with.id}/mission-plan")
        data = resp.json()
        assert "altitude_m" in data
        assert "speed_ms" in data
        assert "estimated_duration_min" in data
        assert "batteries_needed" in data
        assert "area_hectares" in data
        assert "pattern" in data

    def test_mission_plan_400_no_boundary(self, client, db):
        farm, f_with, f_no = _seed_mission_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/{f_no.id}/mission-plan")
        assert resp.status_code == 400

    def test_mission_plan_404_missing_farm(self, client, db):
        resp = client.get("/api/farms/9999/fields/1/mission-plan")
        assert resp.status_code == 404

    def test_mission_plan_404_missing_field(self, client, db):
        farm, f_with, f_no = _seed_mission_data(db)
        resp = client.get(f"/api/farms/{farm.id}/fields/9999/mission-plan")
        assert resp.status_code == 404


class TestMissionPageContent:
    """Page HTML has correct structure for mission rendering."""

    def test_page_has_mision_link_in_nav(self, client):
        resp = client.get("/mision")
        assert "/mision" in resp.text

    def test_page_has_waypoints_container(self, client):
        resp = client.get("/mision")
        assert 'id="mission-waypoints"' in resp.text

    def test_page_has_content_container(self, client):
        resp = client.get("/mision")
        assert 'id="mission-content"' in resp.text

    def test_page_has_flight_params_section(self, client):
        resp = client.get("/mision")
        html = resp.text
        assert "mission-altitude" in html or "mission-speed" in html
