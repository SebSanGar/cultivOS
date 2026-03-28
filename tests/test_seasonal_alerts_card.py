"""Tests for the seasonal risk alerts card on the field detail page."""

import pytest


@pytest.fixture
def farm_for_alerts(client, admin_headers):
    """Create a farm in Jalisco for seasonal alerts testing."""
    farm = client.post("/api/farms", json={
        "name": "Rancho Estacional",
        "owner_name": "Test Owner",
        "location_lat": 20.67,
        "location_lon": -103.35,
        "total_hectares": 25,
        "municipality": "Zapopan",
        "state": "Jalisco",
        "country": "MX",
    }, headers=admin_headers).json()
    return farm


# ── HTML structure tests ──

def test_seasonal_alerts_section_in_html(client):
    """Field detail HTML has the seasonal alerts section container."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    text = resp.text
    assert 'id="section-seasonal-alerts"' in text
    assert 'Alertas Estacionales' in text


def test_seasonal_alerts_placeholder(client):
    """Seasonal alerts section shows a placeholder when empty."""
    resp = client.get("/campo")
    text = resp.text
    assert 'id="seasonal-alerts-content"' in text
    assert 'Sin alertas estacionales' in text


# ── API response tests ──

def test_seasonal_alerts_endpoint_returns_data(client, farm_for_alerts):
    """GET /api/farms/{id}/seasonal-alerts returns season and alerts list."""
    fid = farm_for_alerts["id"]
    resp = client.get(f"/api/farms/{fid}/seasonal-alerts")
    assert resp.status_code == 200
    data = resp.json()
    assert "season" in data
    assert "alerts" in data
    assert isinstance(data["alerts"], list)
    assert data["farm_id"] == fid


def test_seasonal_alerts_with_reference_date(client, farm_for_alerts):
    """Seasonal alerts accept a reference_date override."""
    fid = farm_for_alerts["id"]
    # July = temporal season in Jalisco
    resp = client.get(f"/api/farms/{fid}/seasonal-alerts?reference_date=2026-07-15")
    assert resp.status_code == 200
    data = resp.json()
    assert data["season"] == "temporal"
    assert data["reference_date"] == "2026-07-15"


def test_seasonal_alerts_secas_season(client, farm_for_alerts):
    """Seasonal alerts for January return secas season."""
    fid = farm_for_alerts["id"]
    resp = client.get(f"/api/farms/{fid}/seasonal-alerts?reference_date=2026-01-15")
    assert resp.status_code == 200
    data = resp.json()
    assert data["season"] == "secas"


def test_seasonal_alerts_alert_structure(client, farm_for_alerts):
    """Each alert has crop, alert_type, message, season, month_range."""
    fid = farm_for_alerts["id"]
    resp = client.get(f"/api/farms/{fid}/seasonal-alerts?reference_date=2026-07-15")
    data = resp.json()
    if data["alerts"]:
        alert = data["alerts"][0]
        assert "crop" in alert
        assert "alert_type" in alert
        assert "message" in alert
        assert "season" in alert
        assert "month_range" in alert


def test_seasonal_alerts_404_nonexistent_farm(client):
    """Seasonal alerts return 404 for non-existent farm."""
    resp = client.get("/api/farms/99999/seasonal-alerts")
    assert resp.status_code == 404


# ── JS rendering reference tests ──

def test_field_js_references_seasonal_alerts(client):
    """field.js contains the renderSeasonalAlerts function."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    text = resp.text
    assert "renderSeasonalAlerts" in text
    assert "seasonal-alerts" in text


def test_field_js_fetches_seasonal_alerts(client):
    """field.js fetches the seasonal-alerts endpoint."""
    resp = client.get("/field.js")
    text = resp.text
    assert "seasonal-alerts" in text
