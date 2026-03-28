"""Tests for the drone mission planning UI on the field detail page."""

import pytest


# ── HTML structure ──

def test_mission_section_in_field_html(client):
    """Field detail HTML has the Plan de Vuelo section."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="section-mission"' in html
    assert "Plan de Vuelo" in html


def test_mission_container_in_html(client):
    """Field detail HTML has a container for mission plan content."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    assert 'id="mission-content"' in resp.text


# ── JS logic ──

def test_field_js_has_mission_render(client):
    """field.js contains the renderMissionPlan function."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "renderMissionPlan" in resp.text


def test_field_js_fetches_mission_plan(client):
    """field.js fetches the /mission-plan endpoint."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "/mission-plan" in resp.text


def test_field_js_shows_duration_and_batteries(client):
    """field.js renders estimated_duration_min and batteries_needed."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    assert "estimated_duration_min" in js
    assert "batteries_needed" in js


def test_field_js_shows_altitude_and_photos(client):
    """field.js renders altitude and photo count."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    assert "altitude_m" in js
    assert "estimated_photos" in js


# ── CSS ──

def test_mission_styles_present(client):
    """styles.css has mission plan styling."""
    resp = client.get("/styles.css")
    assert resp.status_code == 200
    assert "mission" in resp.text


# ── API integration (backend already exists — verify it still works) ──

@pytest.fixture
def farm_with_boundary(client, admin_headers):
    """Create a farm with a field that has boundary coordinates."""
    resp = client.post("/api/farms", json={
        "name": "Rancho Mision",
        "location_lat": 20.6597,
        "location_lon": -103.3496,
        "total_hectares": 50,
    }, headers=admin_headers)
    assert resp.status_code == 201
    farm_id = resp.json()["id"]
    boundary = [
        [-103.350, 20.660],
        [-103.340, 20.660],
        [-103.340, 20.669],
        [-103.350, 20.669],
    ]
    resp = client.post(f"/api/farms/{farm_id}/fields", json={
        "name": "Parcela Drone",
        "crop_type": "maiz",
        "boundary_coordinates": boundary,
    }, headers=admin_headers)
    assert resp.status_code == 201
    field_id = resp.json()["id"]
    return farm_id, field_id


def test_mission_api_returns_plan(client, admin_headers, farm_with_boundary):
    """GET mission-plan returns plan with expected fields for UI rendering."""
    farm_id, field_id = farm_with_boundary
    resp = client.get(
        f"/api/farms/{farm_id}/fields/{field_id}/mission-plan",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    # All fields the UI needs
    assert data["estimated_duration_min"] > 0
    assert data["batteries_needed"] >= 1
    assert data["altitude_m"] > 0
    assert data["estimated_photos"] > 0
    assert data["area_hectares"] > 0
    assert data["total_distance_m"] > 0
    assert data["drone_type"] == "mavic_multispectral"
    assert data["pattern"] == "boustrophedon"
    assert len(data["waypoints"]) >= 4
