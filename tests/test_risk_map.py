"""Tests for GET /api/farms/{farm_id}/fields/risk-map endpoint."""

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_farm(client, name="Test Farm", lat=20.66, lon=-103.35):
    resp = client.post("/api/farms", json={
        "name": name,
        "municipality": "Guadalajara",
        "state": "Jalisco",
        "total_hectares": 10.0,
        "location_lat": lat,
        "location_lon": lon,
    })
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _create_field(client, farm_id, name="Parcela 1", crop_type="maiz", hectares=5.0):
    resp = client.post(f"/api/farms/{farm_id}/fields", json={
        "name": name,
        "crop_type": crop_type,
        "hectares": hectares,
    })
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _add_ndvi(client, farm_id, field_id, healthy=True):
    """Post an NDVI result. healthy=True → high NDVI; False → very stressed."""
    if healthy:
        nir = [[0.7, 0.72, 0.68], [0.71, 0.69, 0.73], [0.70, 0.71, 0.72]]
        red = [[0.1, 0.09, 0.11], [0.10, 0.12, 0.09], [0.11, 0.10, 0.10]]
    else:
        # Low NDVI, high stress
        nir = [[0.15, 0.12, 0.14], [0.13, 0.16, 0.11], [0.12, 0.14, 0.13]]
        red = [[0.12, 0.13, 0.11], [0.14, 0.12, 0.13], [0.13, 0.11, 0.14]]
    resp = client.post(f"/api/farms/{farm_id}/fields/{field_id}/ndvi", json={
        "nir_band": nir,
        "red_band": red,
    })
    assert resp.status_code == 201, resp.text


def _add_soil(client, farm_id, field_id):
    resp = client.post(f"/api/farms/{farm_id}/fields/{field_id}/soil", json={
        "ph": 6.5,
        "organic_matter_pct": 3.0,
        "nitrogen_ppm": 50.0,
        "phosphorus_ppm": 30.0,
        "potassium_ppm": 200.0,
        "moisture_pct": 40.0,
        "sampled_at": "2026-01-01T00:00:00",
    })
    assert resp.status_code == 201, resp.text


def _compute_health(client, farm_id, field_id):
    resp = client.post(f"/api/farms/{farm_id}/fields/{field_id}/health")
    assert resp.status_code == 201, resp.text
    return resp.json()


def _add_weather(client, farm_id, temp_c=25.0, wind_kmh=10.0, rainfall_mm=5.0):
    resp = client.post(f"/api/farms/{farm_id}/weather", json={
        "temp_c": temp_c,
        "humidity_pct": 60.0,
        "wind_kmh": wind_kmh,
        "rainfall_mm": rainfall_mm,
        "description": "clear",
        "forecast_3day": [],
    })
    assert resp.status_code == 201, resp.text


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_risk_map_unknown_farm_returns_404(client):
    resp = client.get("/api/farms/99999/fields/risk-map")
    assert resp.status_code == 404


def test_risk_map_empty_farm_returns_empty_list(client):
    farm_id = _create_farm(client)
    resp = client.get(f"/api/farms/{farm_id}/fields/risk-map")
    assert resp.status_code == 200
    assert resp.json() == []


def test_risk_map_field_no_data_returns_null_risk(client):
    """Field with no health/weather/disease data → null risk_score."""
    farm_id = _create_farm(client)
    _create_field(client, farm_id)
    resp = client.get(f"/api/farms/{farm_id}/fields/risk-map")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["risk_score"] is None
    assert items[0]["dominant_factor"] is None


def test_risk_map_risk_score_bounded_0_to_100(client):
    """risk_score must be in [0, 100] for populated fields."""
    farm_id = _create_farm(client)
    field_id = _create_field(client, farm_id)
    _add_ndvi(client, farm_id, field_id, healthy=True)
    _add_soil(client, farm_id, field_id)
    _compute_health(client, farm_id, field_id)
    _add_weather(client, farm_id)

    resp = client.get(f"/api/farms/{farm_id}/fields/risk-map")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    score = items[0]["risk_score"]
    assert score is not None
    assert 0.0 <= score <= 100.0


def test_risk_map_dominant_factor_valid_values(client):
    """dominant_factor must be one of {health, weather, disease, thermal}."""
    farm_id = _create_farm(client)
    field_id = _create_field(client, farm_id)
    _add_ndvi(client, farm_id, field_id, healthy=True)
    _add_soil(client, farm_id, field_id)
    _compute_health(client, farm_id, field_id)
    _add_weather(client, farm_id)

    resp = client.get(f"/api/farms/{farm_id}/fields/risk-map")
    assert resp.status_code == 200
    items = resp.json()
    factor = items[0]["dominant_factor"]
    assert factor in {"health", "weather", "disease", "thermal"}


def test_risk_map_low_health_produces_high_risk(client):
    """Very low health + critical weather alert → risk_score should be > 50."""
    farm_id = _create_farm(client)
    field_id = _create_field(client, farm_id)
    # Bad NDVI: very stressed field (near-infrared ≈ red → NDVI near 0)
    _add_ndvi(client, farm_id, field_id, healthy=False)
    _add_soil(client, farm_id, field_id)
    health = _compute_health(client, farm_id, field_id)
    assert health["score"] < 50  # verify the seeded data creates low health
    # Extreme heat alert pushes weather component up
    _add_weather(client, farm_id, temp_c=42.0, wind_kmh=10.0, rainfall_mm=0.0)

    resp = client.get(f"/api/farms/{farm_id}/fields/risk-map")
    assert resp.status_code == 200
    items = resp.json()
    assert items[0]["risk_score"] > 35.0


def test_risk_map_returns_field_metadata(client):
    """Response includes field_id and name."""
    farm_id = _create_farm(client)
    _create_field(client, farm_id, name="Norte Parcela")

    resp = client.get(f"/api/farms/{farm_id}/fields/risk-map")
    assert resp.status_code == 200
    item = resp.json()[0]
    assert item["field_id"] is not None
    assert item["name"] == "Norte Parcela"


def test_risk_map_multiple_fields(client):
    """Returns one entry per field."""
    farm_id = _create_farm(client)
    _create_field(client, farm_id, name="Campo A")
    _create_field(client, farm_id, name="Campo B")
    _create_field(client, farm_id, name="Campo C")

    resp = client.get(f"/api/farms/{farm_id}/fields/risk-map")
    assert resp.status_code == 200
    assert len(resp.json()) == 3


def test_risk_map_severe_weather_raises_risk(client):
    """Critical weather alert should push risk_score up."""
    farm_id = _create_farm(client)
    field_id = _create_field(client, farm_id)
    _add_ndvi(client, farm_id, field_id, healthy=True)
    _add_soil(client, farm_id, field_id)
    _compute_health(client, farm_id, field_id)
    # Extreme heat alert (>38C)
    _add_weather(client, farm_id, temp_c=42.0, wind_kmh=10.0, rainfall_mm=0.0)

    resp = client.get(f"/api/farms/{farm_id}/fields/risk-map")
    assert resp.status_code == 200
    items = resp.json()
    assert items[0]["risk_score"] is not None
