"""Tests for the field detail frontend page (/campo)."""

import pytest


@pytest.fixture
def farm_with_full_data(client, admin_headers):
    """Create a farm with a field that has all Cerebro data sources."""
    farm = client.post("/api/farms", json={
        "name": "Rancho Test",
        "owner_name": "Test Owner",
        "location_lat": 20.67,
        "location_lon": -103.35,
        "total_hectares": 30,
        "municipality": "Zapopan",
        "state": "Jalisco",
        "country": "MX",
    }, headers=admin_headers).json()

    field = client.post(f"/api/farms/{farm['id']}/fields", json={
        "name": "Parcela Cerebro",
        "crop_type": "maiz",
        "hectares": 15,
    }).json()

    # Soil
    soil_resp = client.post(f"/api/farms/{farm['id']}/fields/{field['id']}/soil", json={
        "ph": 6.5,
        "organic_matter_pct": 3.0,
        "nitrogen_ppm": 40,
        "phosphorus_ppm": 25,
        "potassium_ppm": 200,
        "texture": "franco",
        "moisture_pct": 30,
        "sampled_at": "2026-03-20T10:00:00",
    })
    assert soil_resp.status_code == 201, f"Soil POST failed: {soil_resp.text}"

    # NDVI
    client.post(f"/api/farms/{farm['id']}/fields/{field['id']}/ndvi", json={
        "nir_band": [[0.5, 0.6, 0.55], [0.58, 0.62, 0.57], [0.54, 0.59, 0.56]],
        "red_band": [[0.1, 0.08, 0.09], [0.07, 0.06, 0.08], [0.1, 0.07, 0.09]],
    })

    # Thermal
    client.post(f"/api/farms/{farm['id']}/fields/{field['id']}/thermal", json={
        "thermal_band": [[32.0, 33.0, 31.5], [34.0, 36.0, 33.0], [31.0, 32.5, 34.5]],
    })

    # Health
    client.post(f"/api/farms/{farm['id']}/fields/{field['id']}/health")

    return {"farm": farm, "field": field}


def test_field_detail_page_loads(client):
    """GET /campo returns 200 with HTML containing field detail markers."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    html = resp.text
    assert "cultivOS" in html
    assert "Detalle de Campo" in html


def test_field_sections_present(client):
    """Field detail HTML has containers for all Cerebro intelligence sections."""
    resp = client.get("/campo")
    html = resp.text
    # All major sections should have container divs
    assert 'id="section-ndvi"' in html
    assert 'id="section-thermal"' in html
    assert 'id="section-soil"' in html
    assert 'id="section-treatments"' in html
    assert 'id="section-irrigation"' in html
    assert 'id="section-rotation"' in html


def test_field_health_chart(client):
    """Field detail HTML has a health history chart container."""
    resp = client.get("/campo")
    html = resp.text
    assert 'id="health-chart"' in html


def test_field_detail_apis_respond(client, farm_with_full_data):
    """All field-level APIs return data for a field with full Cerebro data."""
    farm = farm_with_full_data["farm"]
    field = farm_with_full_data["field"]
    base = f"/api/farms/{farm['id']}/fields/{field['id']}"

    # Health
    resp = client.get(f"{base}/health")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # NDVI
    resp = client.get(f"{base}/ndvi")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # Thermal
    resp = client.get(f"{base}/thermal")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # Soil
    resp = client.get(f"{base}/soil")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # Treatments
    resp = client.get(f"{base}/treatments")
    assert resp.status_code == 200

    # Irrigation
    resp = client.get(f"{base}/irrigation")
    assert resp.status_code == 200

    # Rotation
    resp = client.get(f"{base}/rotation")
    assert resp.status_code == 200


def test_field_detail_spanish_labels(client):
    """Field detail HTML uses Spanish labels."""
    resp = client.get("/campo")
    html = resp.text
    assert "Salud" in html
    assert "Suelo" in html
    assert "Riego" in html
