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


# ── Sparkline tests ──

def test_sparkline_trend_data_available(client, farm_with_data):
    """Health trend endpoint returns trend direction for sparkline coloring."""
    farm = farm_with_data["farm"]
    field = farm_with_data["fields"][0]
    # Compute additional health scores to get meaningful trend data
    # (first score was added in fixture)
    client.post(f"/api/farms/{farm['id']}/fields/{field['id']}/health")
    client.post(f"/api/farms/{farm['id']}/fields/{field['id']}/health")

    resp = client.get(
        f"/api/farms/{farm['id']}/fields/{field['id']}/health/trend"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["trend"] in ("improving", "stable", "declining", "insufficient_data")
    assert data["data_points"] >= 1


def test_sparkline_history_scores(client, farm_with_data):
    """Health history returns chronological scores the sparkline will plot."""
    farm = farm_with_data["farm"]
    field = farm_with_data["fields"][0]
    # Add more health scores to have enough history for a sparkline
    for _ in range(4):
        client.post(f"/api/farms/{farm['id']}/fields/{field['id']}/health")

    resp = client.get(
        f"/api/farms/{farm['id']}/fields/{field['id']}/health/history"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 5
    # Scores are chronological (oldest first)
    assert len(data["scores"]) >= 5
    for s in data["scores"]:
        assert 0 <= s["score"] <= 100


def test_sparkline_handles_insufficient_data(client, admin_headers):
    """Trend returns insufficient_data when field has <3 health scores."""
    farm = client.post("/api/farms", json={
        "name": "Rancho Nuevo",
        "owner_name": "Maria",
        "location_lat": 20.5,
        "location_lon": -103.2,
        "total_hectares": 10,
        "municipality": "Tlajomulco",
        "state": "Jalisco",
        "country": "MX",
    }, headers=admin_headers).json()
    f = client.post(f"/api/farms/{farm['id']}/fields", json={
        "name": "Campo Chico",
        "crop_type": "frijol",
        "hectares": 5,
    }).json()
    # Add NDVI so health can be computed
    client.post(f"/api/farms/{farm['id']}/fields/{f['id']}/ndvi", json={
        "nir_band": [[0.5, 0.6], [0.55, 0.58]],
        "red_band": [[0.1, 0.08], [0.09, 0.07]],
    })
    # Only one health score — not enough for trend
    client.post(f"/api/farms/{farm['id']}/fields/{f['id']}/health")

    resp = client.get(
        f"/api/farms/{farm['id']}/fields/{f['id']}/health/trend"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["trend"] == "insufficient_data"
    assert data["data_points"] == 1


def test_dashboard_contains_sparkline_code(client):
    """Dashboard JS includes the sparkline rendering function."""
    resp = client.get("/app.js")
    assert resp.status_code == 200
    js = resp.text
    assert "buildSparkline" in js
    assert "<svg" in js.lower() or "svg" in js


def test_dashboard_contains_sparkline_styles(client):
    """Dashboard CSS includes sparkline styling."""
    resp = client.get("/styles.css")
    assert resp.status_code == 200
    css = resp.text
    assert "sparkline" in css
