"""Tests for GET /api/farms/{farm_id}/fields/{field_id}/forecast-alerts."""

import pytest
from datetime import datetime, date, timedelta

from cultivos.db.models import (
    Farm, Field, WeatherRecord, HealthScore, SoilAnalysis, NDVIResult
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_farm(db, name="Rancho Pronóstico"):
    farm = Farm(name=name, state="Jalisco")
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id, name="Campo Riesgo", crop_type="maiz"):
    field = Field(farm_id=farm_id, name=name, crop_type=crop_type)
    db.add(field)
    db.commit()
    return field


def _make_weather(db, farm_id, temp_c=25.0, humidity_pct=50.0):
    w = WeatherRecord(
        farm_id=farm_id,
        temp_c=temp_c,
        humidity_pct=humidity_pct,
        wind_kmh=8.0,
        rainfall_mm=0.0,
        description="sunny",
        forecast_3day=[],
    )
    db.add(w)
    db.commit()
    return w


def _make_health(db, field_id, score=75.0):
    h = HealthScore(
        field_id=field_id,
        score=score,
        sources=["ndvi"],
        breakdown={},
    )
    db.add(h)
    db.commit()
    return h


def _make_soil(db, field_id, ph=6.5, moisture_pct=50.0):
    s = SoilAnalysis(
        field_id=field_id,
        ph=ph,
        moisture_pct=moisture_pct,
        sampled_at=datetime(2026, 4, 1),
    )
    db.add(s)
    db.commit()
    return s


def _make_ndvi(db, field_id, ndvi_mean=0.65):
    n = NDVIResult(
        field_id=field_id,
        ndvi_mean=ndvi_mean,
        ndvi_std=0.1,
        ndvi_min=0.4,
        ndvi_max=0.9,
        pixels_total=1000,
        stress_pct=5.0,
        zones=[],
    )
    db.add(n)
    db.commit()
    return n


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_response_keys_present(client, db):
    """Response contains all required schema keys."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/forecast-alerts")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "field_id" in data
    assert "forecast_date" in data
    assert "projected_risk_level" in data
    assert "risk_drivers" in data
    assert "preventive_actions_es" in data


def test_404_unknown_farm(client):
    """Unknown farm → 404."""
    resp = client.get("/api/farms/99999/fields/1/forecast-alerts")
    assert resp.status_code == 404


def test_404_unknown_field(client, db):
    """Unknown field → 404."""
    farm = _make_farm(db)
    resp = client.get(f"/api/farms/{farm.id}/fields/99999/forecast-alerts")
    assert resp.status_code == 404


def test_no_weather_data_defaults_low(client, db):
    """No weather data → projected_risk_level = low (safe default)."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    # No weather, no health, no soil

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/forecast-alerts")
    assert resp.status_code == 200
    assert resp.json()["projected_risk_level"] == "low"


def test_high_disease_risk_returns_high(client, db):
    """High disease risk conditions → projected_risk_level = high."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    # Conditions that trigger disease risk score >= 50:
    # humidity > 70% (+20) + soil pH < 5.5 (+15) + temp > 35°C (+10) = 45 → add NDVI drop
    _make_weather(db, farm.id, temp_c=38.0, humidity_pct=75.0)  # +20 humidity, +10 temp
    _make_soil(db, field.id, ph=5.0)  # +15 pH
    # Two NDVI records to trigger MoM drop > 20%
    from cultivos.db.models import NDVIResult
    from datetime import timedelta
    n1 = NDVIResult(
        field_id=field.id, ndvi_mean=0.8, ndvi_std=0.1,
        ndvi_min=0.5, ndvi_max=0.9, pixels_total=1000, stress_pct=5.0, zones=[],
        analyzed_at=datetime.utcnow() - timedelta(days=35),
    )
    n2 = NDVIResult(
        field_id=field.id, ndvi_mean=0.5, ndvi_std=0.1,
        ndvi_min=0.3, ndvi_max=0.7, pixels_total=1000, stress_pct=20.0, zones=[],
        analyzed_at=datetime.utcnow(),
    )
    db.add_all([n1, n2])
    db.commit()
    _make_health(db, field.id, score=35.0)  # low health

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/forecast-alerts")
    assert resp.status_code == 200
    assert resp.json()["projected_risk_level"] == "high"


def test_low_risk_normal_conditions(client, db):
    """Good health + normal weather → low projected risk."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _make_weather(db, farm.id, temp_c=22.0, humidity_pct=50.0)
    _make_health(db, field.id, score=80.0)
    _make_soil(db, field.id, ph=6.5, moisture_pct=55.0)
    _make_ndvi(db, field.id, ndvi_mean=0.7)

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/forecast-alerts")
    assert resp.status_code == 200
    assert resp.json()["projected_risk_level"] == "low"


def test_risk_drivers_is_list_of_strings(client, db):
    """risk_drivers is a list (possibly empty)."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/forecast-alerts")
    assert resp.status_code == 200
    drivers = resp.json()["risk_drivers"]
    assert isinstance(drivers, list)
    for d in drivers:
        assert isinstance(d, str)


def test_forecast_date_is_3_days_ahead(client, db):
    """forecast_date is approximately today + 3 days."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/forecast-alerts")
    assert resp.status_code == 200
    forecast_date = resp.json()["forecast_date"]
    expected = (date.today() + timedelta(days=3)).isoformat()
    assert forecast_date == expected


def test_preventive_actions_non_empty_for_medium_risk(client, db):
    """preventive_actions_es is non-empty for non-low risk."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    # Conditions for medium risk: humidity > 60%
    _make_weather(db, farm.id, temp_c=25.0, humidity_pct=65.0)
    _make_health(db, field.id, score=55.0)  # health < 60

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/forecast-alerts")
    assert resp.status_code == 200
    data = resp.json()
    if data["projected_risk_level"] != "low":
        assert len(data["preventive_actions_es"]) > 0
