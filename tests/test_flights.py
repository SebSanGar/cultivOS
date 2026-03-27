"""Tests for drone flight logging API."""

import pytest
from cultivos.db.models import Farm, Field, FlightLog, NDVIResult
from datetime import datetime


@pytest.fixture
def farm_and_field(db):
    farm = Farm(name="Rancho Vuelo", owner_name="Carlos", location_lat=20.6, location_lon=-103.3)
    db.add(farm)
    db.commit()
    db.refresh(farm)
    field = Field(farm_id=farm.id, name="Parcela Norte", crop_type="maiz", hectares=15.0)
    db.add(field)
    db.commit()
    db.refresh(field)
    return farm, field


def test_log_flight(client, admin_headers, farm_and_field):
    """POST /api/farms/{id}/fields/{id}/flights creates flight record."""
    farm, field = farm_and_field
    resp = client.post(
        f"/api/farms/{farm.id}/fields/{field.id}/flights",
        json={
            "drone_type": "mavic_multispectral",
            "mission_type": "health_scan",
            "flight_date": "2026-03-27T10:00:00",
            "duration_minutes": 45.5,
            "altitude_m": 120.0,
            "images_count": 230,
            "coverage_pct": 95.0,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["drone_type"] == "mavic_multispectral"
    assert data["duration_minutes"] == 45.5
    assert data["altitude_m"] == 120.0
    assert data["status"] == "pending"
    assert data["field_id"] == field.id


def test_link_flight_to_ndvi(client, admin_headers, db, farm_and_field):
    """Flight record can be linked to NDVI result via flight_id FK."""
    farm, field = farm_and_field
    # Create flight
    resp = client.post(
        f"/api/farms/{farm.id}/fields/{field.id}/flights",
        json={
            "drone_type": "mavic_multispectral",
            "flight_date": "2026-03-27T10:00:00",
            "duration_minutes": 30.0,
            "altitude_m": 100.0,
        },
        headers=admin_headers,
    )
    flight_id = resp.json()["id"]

    # Create NDVI result linked to this flight
    ndvi = NDVIResult(
        field_id=field.id,
        flight_id=flight_id,
        ndvi_mean=0.65,
        ndvi_std=0.1,
        ndvi_min=0.2,
        ndvi_max=0.9,
        pixels_total=10000,
        stress_pct=12.5,
        zones=[],
    )
    db.add(ndvi)
    db.commit()
    db.refresh(ndvi)

    assert ndvi.flight_id == flight_id


def test_flight_history(client, admin_headers, farm_and_field):
    """GET /api/farms/{id}/fields/{id}/flights returns chronological list."""
    farm, field = farm_and_field
    # Create two flights
    for i, date in enumerate(["2026-03-25T08:00:00", "2026-03-27T10:00:00"]):
        client.post(
            f"/api/farms/{farm.id}/fields/{field.id}/flights",
            json={
                "drone_type": "mavic_multispectral",
                "flight_date": date,
                "duration_minutes": 30.0 + i * 10,
                "altitude_m": 100.0,
            },
            headers=admin_headers,
        )

    resp = client.get(
        f"/api/farms/{farm.id}/fields/{field.id}/flights",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    # Most recent first
    assert data[0]["flight_date"] > data[1]["flight_date"]


def test_flight_stats(client, admin_headers, farm_and_field):
    """GET /api/farms/{id}/fields/{id}/flights/stats returns aggregated stats."""
    farm, field = farm_and_field
    flights = [
        {"drone_type": "mavic_multispectral", "flight_date": "2026-03-25T08:00:00",
         "duration_minutes": 60.0, "altitude_m": 120.0, "coverage_pct": 50.0},
        {"drone_type": "mavic_thermal", "flight_date": "2026-03-26T09:00:00",
         "duration_minutes": 30.0, "altitude_m": 100.0, "coverage_pct": 40.0},
        {"drone_type": "mavic_multispectral", "flight_date": "2026-03-27T10:00:00",
         "duration_minutes": 45.0, "altitude_m": 120.0, "coverage_pct": 60.0},
    ]
    for f in flights:
        client.post(
            f"/api/farms/{farm.id}/fields/{field.id}/flights",
            json=f,
            headers=admin_headers,
        )

    resp = client.get(
        f"/api/farms/{farm.id}/fields/{field.id}/flights/stats",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_flights"] == 3
    assert data["total_hours"] == pytest.approx(2.25)  # (60+30+45)/60
    assert data["drone_breakdown"]["mavic_multispectral"] == 2
    assert data["drone_breakdown"]["mavic_thermal"] == 1


def test_flight_404_farm(client, admin_headers):
    """Returns 404 for nonexistent farm."""
    resp = client.post(
        "/api/farms/999/fields/1/flights",
        json={
            "drone_type": "mavic_multispectral",
            "flight_date": "2026-03-27T10:00:00",
            "duration_minutes": 30.0,
            "altitude_m": 100.0,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 404
