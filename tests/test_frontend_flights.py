"""Tests for the flight log history UI on the field detail page."""

import pytest


# ── HTML structure ──

def test_flights_section_in_field_html(client):
    """Field detail HTML has the Historial de Vuelos section."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="section-flights"' in html
    assert "Historial de Vuelos" in html


def test_flights_container_in_html(client):
    """Field detail HTML has containers for flights content and stats."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="flights-content"' in html
    assert 'id="flights-stats"' in html


# ── JS logic ──

def test_field_js_has_render_flights(client):
    """field.js contains the renderFlights function."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "renderFlights" in resp.text


def test_field_js_fetches_flights(client):
    """field.js fetches the /flights endpoint."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "/flights" in resp.text


def test_field_js_fetches_flight_stats(client):
    """field.js fetches the /flights/stats endpoint."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "/flights/stats" in resp.text


def test_field_js_shows_drone_type(client):
    """field.js renders drone_type for each flight."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "drone_type" in resp.text


def test_field_js_shows_flight_date(client):
    """field.js renders flight_date for each flight."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "flight_date" in resp.text


def test_field_js_shows_duration_and_coverage(client):
    """field.js renders duration_minutes and coverage_pct."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    assert "duration_minutes" in js
    assert "coverage_pct" in js


def test_field_js_shows_stats_totals(client):
    """field.js renders total_flights and total_hours from stats."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    assert "total_flights" in js
    assert "total_hours" in js


def test_field_js_handles_no_flights(client):
    """field.js handles empty flight list gracefully."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "Sin vuelos registrados" in resp.text


# ── API integration ──

@pytest.fixture
def farm_field(client, admin_headers):
    """Create a farm with a field for flight tests."""
    resp = client.post("/api/farms", json={
        "name": "Rancho Vuelos",
        "location_lat": 20.6597,
        "location_lon": -103.3496,
        "total_hectares": 50,
    }, headers=admin_headers)
    assert resp.status_code == 201
    farm_id = resp.json()["id"]
    resp = client.post(f"/api/farms/{farm_id}/fields", json={
        "name": "Parcela Test",
        "crop_type": "maiz",
    }, headers=admin_headers)
    assert resp.status_code == 201
    field_id = resp.json()["id"]
    return farm_id, field_id


def test_flights_api_returns_list(client, admin_headers, farm_field):
    """GET /flights returns an empty list when no flights exist."""
    farm_id, field_id = farm_field
    resp = client.get(
        f"/api/farms/{farm_id}/fields/{field_id}/flights",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json() == []


def test_flights_stats_empty(client, admin_headers, farm_field):
    """GET /flights/stats returns zeros when no flights exist."""
    farm_id, field_id = farm_field
    resp = client.get(
        f"/api/farms/{farm_id}/fields/{field_id}/flights/stats",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_flights"] == 0
    assert data["total_hours"] == 0


def test_flights_log_and_stats(client, admin_headers, farm_field):
    """POST a flight, then verify it appears in list and stats."""
    farm_id, field_id = farm_field
    flight = {
        "drone_type": "mavic_multispectral",
        "mission_type": "health_scan",
        "flight_date": "2026-03-15T10:00:00",
        "duration_minutes": 45.0,
        "altitude_m": 80.0,
        "images_count": 120,
        "coverage_pct": 85.5,
    }
    resp = client.post(
        f"/api/farms/{farm_id}/fields/{field_id}/flights",
        json=flight,
        headers=admin_headers,
    )
    assert resp.status_code == 201

    # List should contain the flight
    resp = client.get(
        f"/api/farms/{farm_id}/fields/{field_id}/flights",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    flights = resp.json()
    assert len(flights) == 1
    assert flights[0]["drone_type"] == "mavic_multispectral"
    assert flights[0]["duration_minutes"] == 45.0

    # Stats should reflect the flight
    resp = client.get(
        f"/api/farms/{farm_id}/fields/{field_id}/flights/stats",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_flights"] == 1
    assert data["total_hours"] == 0.75  # 45 min / 60
