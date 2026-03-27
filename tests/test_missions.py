"""Tests for drone mission planning from field boundaries."""

import pytest


# ── Fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def farm_and_field(client, admin_headers):
    """Create a farm with a field that has boundary coordinates."""
    resp = client.post("/api/farms", json={
        "name": "Rancho Prueba",
        "location_lat": 20.6597,
        "location_lon": -103.3496,
        "total_hectares": 50,
    }, headers=admin_headers)
    assert resp.status_code == 201
    farm_id = resp.json()["id"]

    # Roughly 10 hectares rectangular field near Guadalajara
    boundary = [
        [-103.350, 20.660],
        [-103.340, 20.660],
        [-103.340, 20.669],
        [-103.350, 20.669],
    ]
    resp = client.post(f"/api/farms/{farm_id}/fields", json={
        "name": "Parcela Norte",
        "crop_type": "maiz",
        "boundary_coordinates": boundary,
    }, headers=admin_headers)
    assert resp.status_code == 201
    field_id = resp.json()["id"]
    return farm_id, field_id, boundary


# ── Pure function tests ────────────────────────────────────────────────

def test_generate_waypoints(farm_and_field):
    """Field boundary polygon -> GPS waypoint list."""
    from cultivos.services.drone.mission import generate_mission_plan

    _, _, boundary = farm_and_field
    plan = generate_mission_plan(
        boundary_coordinates=boundary,
        mission_type="health_scan",
        drone_type="mavic_multispectral",
    )
    assert "waypoints" in plan
    assert len(plan["waypoints"]) >= 4  # at least start corners
    # Each waypoint must be [lon, lat]
    for wp in plan["waypoints"]:
        assert len(wp) == 2
        assert isinstance(wp[0], float)
        assert isinstance(wp[1], float)


def test_coverage_pattern(farm_and_field):
    """Boustrophedon pattern covering entire field."""
    from cultivos.services.drone.mission import generate_mission_plan

    _, _, boundary = farm_and_field
    plan = generate_mission_plan(
        boundary_coordinates=boundary,
        mission_type="health_scan",
        drone_type="mavic_multispectral",
    )
    # Pattern must be boustrophedon (alternating direction)
    assert plan["pattern"] == "boustrophedon"
    # Waypoints should span the full field width (lon range)
    lons = [wp[0] for wp in plan["waypoints"]]
    min_lon = min(c[0] for c in boundary)
    max_lon = max(c[0] for c in boundary)
    assert min(lons) <= min_lon + 0.001  # close to boundary edge
    assert max(lons) >= max_lon - 0.001


def test_overlap_percentage(farm_and_field):
    """70% adjacent line overlap."""
    from cultivos.services.drone.mission import generate_mission_plan

    _, _, boundary = farm_and_field
    plan = generate_mission_plan(
        boundary_coordinates=boundary,
        mission_type="health_scan",
        drone_type="mavic_multispectral",
    )
    assert plan["overlap_pct"] == 70
    # Line spacing should reflect 70% overlap at given altitude
    assert plan["line_spacing_m"] > 0


def test_mission_metadata(farm_and_field):
    """Estimated flight time, distance, photo count."""
    from cultivos.services.drone.mission import generate_mission_plan

    _, _, boundary = farm_and_field
    plan = generate_mission_plan(
        boundary_coordinates=boundary,
        mission_type="health_scan",
        drone_type="mavic_multispectral",
    )
    assert plan["estimated_duration_min"] > 0
    assert plan["total_distance_m"] > 0
    assert plan["estimated_photos"] > 0
    assert plan["altitude_m"] > 0
    assert plan["speed_ms"] > 0
    assert plan["batteries_needed"] >= 1
    assert plan["area_hectares"] > 0
    assert plan["drone_type"] == "mavic_multispectral"
    assert plan["mission_type"] == "health_scan"


# ── API endpoint tests ─────────────────────────────────────────────────

def test_api_mission_plan_success(client, admin_headers, farm_and_field):
    """GET /api/farms/{id}/fields/{id}/mission-plan returns a plan."""
    farm_id, field_id, _ = farm_and_field
    resp = client.get(
        f"/api/farms/{farm_id}/fields/{field_id}/mission-plan",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["pattern"] == "boustrophedon"
    assert len(data["waypoints"]) >= 4
    assert data["estimated_duration_min"] > 0
    assert data["batteries_needed"] >= 1


def test_api_mission_plan_no_boundary(client, admin_headers):
    """Field without boundary coordinates → 400."""
    resp = client.post("/api/farms", json={
        "name": "Rancho Sin Limites",
    }, headers=admin_headers)
    farm_id = resp.json()["id"]
    resp = client.post(f"/api/farms/{farm_id}/fields", json={
        "name": "Campo Abierto",
    }, headers=admin_headers)
    field_id = resp.json()["id"]
    resp = client.get(
        f"/api/farms/{farm_id}/fields/{field_id}/mission-plan",
        headers=admin_headers,
    )
    assert resp.status_code == 400
    assert "boundary" in resp.json()["error"]["message"].lower()


def test_api_mission_plan_custom_params(client, admin_headers, farm_and_field):
    """Query params override mission type and drone type."""
    farm_id, field_id, _ = farm_and_field
    resp = client.get(
        f"/api/farms/{farm_id}/fields/{field_id}/mission-plan"
        "?mission_type=thermal_check&drone_type=mavic_thermal",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["drone_type"] == "mavic_thermal"
    assert data["mission_type"] == "thermal_check"
    # Thermal flights are at lower altitude
    assert data["altitude_m"] <= 100


def test_api_mission_plan_field_not_found(client, admin_headers):
    """Non-existent field → 404."""
    resp = client.post("/api/farms", json={"name": "Test"}, headers=admin_headers)
    farm_id = resp.json()["id"]
    resp = client.get(
        f"/api/farms/{farm_id}/fields/9999/mission-plan",
        headers=admin_headers,
    )
    assert resp.status_code == 404
