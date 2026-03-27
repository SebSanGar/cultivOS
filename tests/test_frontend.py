"""Tests for the farm dashboard frontend."""

import pytest


@pytest.fixture
def farm_with_data(client, admin_headers):
    """Create a farm with fields, soil, NDVI, and health data for dashboard testing."""
    # Create farm
    farm = client.post("/api/farms", json={
        "name": "Rancho El Sol",
        "owner_name": "Juan Pérez",
        "location_lat": 20.67,
        "location_lon": -103.35,
        "total_hectares": 50,
        "municipality": "Zapopan",
        "state": "Jalisco",
        "country": "MX",
    }, headers=admin_headers).json()

    # Create two fields
    f1 = client.post(f"/api/farms/{farm['id']}/fields", json={
        "name": "Parcela Norte",
        "crop_type": "maíz",
        "hectares": 25,
    }).json()
    f2 = client.post(f"/api/farms/{farm['id']}/fields", json={
        "name": "Parcela Sur",
        "crop_type": "aguacate",
        "hectares": 25,
    }).json()

    # Add soil analysis to field 1
    client.post(f"/api/farms/{farm['id']}/fields/{f1['id']}/soil", json={
        "ph": 6.5,
        "organic_matter_pct": 3.0,
        "nitrogen_ppm": 40,
        "phosphorus_ppm": 25,
        "potassium_ppm": 200,
        "texture": "franco",
        "moisture_pct": 30,
    })

    # Add NDVI to field 1 (simple 3x3 array with healthy values)
    client.post(f"/api/farms/{farm['id']}/fields/{f1['id']}/ndvi", json={
        "nir_band": [[0.5, 0.6, 0.55], [0.58, 0.62, 0.57], [0.54, 0.59, 0.56]],
        "red_band": [[0.1, 0.08, 0.09], [0.07, 0.06, 0.08], [0.1, 0.07, 0.09]],
    })

    # Compute health score for field 1
    client.post(f"/api/farms/{farm['id']}/fields/{f1['id']}/health")

    return {"farm": farm, "fields": [f1, f2]}


def test_dashboard_page_loads(client):
    """GET / returns 200 with HTML containing 'cultivOS'."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "cultivOS" in resp.text


def test_dashboard_fetches_farms(client, admin_headers, farm_with_data):
    """GET /api/farms returns farm data that the dashboard JS will fetch."""
    resp = client.get("/api/farms", headers=admin_headers)
    assert resp.status_code == 200
    farms = resp.json()["data"]
    assert len(farms) >= 1
    assert farms[0]["name"] == "Rancho El Sol"


def test_dashboard_shows_health_score(client, farm_with_data):
    """Health score endpoint returns a score that will be color-coded on dashboard."""
    farm = farm_with_data["farm"]
    field = farm_with_data["fields"][0]
    resp = client.get(f"/api/farms/{farm['id']}/fields/{field['id']}/health")
    assert resp.status_code == 200
    scores = resp.json()
    assert len(scores) >= 1
    score = scores[0]["score"]
    # Score should be between 0 and 100
    assert 0 <= score <= 100


def test_dashboard_shows_field_list(client, farm_with_data):
    """Clicking a farm shows its fields with crop type."""
    farm = farm_with_data["farm"]
    resp = client.get(f"/api/farms/{farm['id']}/fields")
    assert resp.status_code == 200
    fields = resp.json()
    assert len(fields) == 2
    crop_types = {f["crop_type"] for f in fields}
    assert "maíz" in crop_types
    assert "aguacate" in crop_types


def test_dashboard_spanish_labels(client):
    """Dashboard HTML contains Spanish labels."""
    resp = client.get("/")
    html = resp.text
    # Check for key Spanish labels that should be in the dashboard
    assert "Granjas" in html or "granjas" in html
    assert "Campos" in html or "campos" in html
    assert "Salud" in html or "salud" in html
