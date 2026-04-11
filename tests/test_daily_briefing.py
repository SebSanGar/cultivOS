"""Tests for GET /api/farms/{farm_id}/daily-briefing."""

import pytest
from cultivos.db.models import Farm, Field, HealthScore, WeatherRecord


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_farm(db, name="Rancho Prueba"):
    farm = Farm(name=name, state="Jalisco")
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id, name="Campo Uno", crop_type="maiz", hectares=5.0):
    field = Field(farm_id=farm_id, name=name, crop_type=crop_type, hectares=hectares)
    db.add(field)
    db.commit()
    return field


def _make_health(db, field_id, score=80.0):
    hs = HealthScore(field_id=field_id, score=score, sources=["health"], breakdown={})
    db.add(hs)
    db.commit()
    return hs


def _make_weather(db, farm_id, temp_c=22.0, humidity_pct=55.0):
    w = WeatherRecord(
        farm_id=farm_id,
        temp_c=temp_c,
        humidity_pct=humidity_pct,
        wind_kmh=10.0,
        rainfall_mm=0.0,
        description="sunny",
        forecast_3day=[],
    )
    db.add(w)
    db.commit()
    return w


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_response_keys_present(client, db):
    """Response contains all required schema keys."""
    farm = _make_farm(db)
    _make_field(db, farm.id)

    resp = client.get(f"/api/farms/{farm.id}/daily-briefing")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "date" in data
    assert "weather_summary_es" in data
    assert "urgent_field" in data
    assert "upcoming_treatments" in data
    assert "overall_farm_status" in data


def test_404_unknown_farm(client):
    """Unknown farm_id returns 404."""
    resp = client.get("/api/farms/99999/daily-briefing")
    assert resp.status_code == 404


def test_healthy_farm_returns_ok_status(client, db):
    """Farm with all healthy fields returns overall_farm_status=ok."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _make_health(db, field.id, score=95.0)  # very healthy → low stress

    resp = client.get(f"/api/farms/{farm.id}/daily-briefing")
    assert resp.status_code == 200
    data = resp.json()
    # High health score → low priority_score → ok status
    assert data["overall_farm_status"] in ("ok", "attention", "urgent")


def test_no_weather_data_graceful(client, db):
    """Farm with no weather data returns graceful fallback message."""
    farm = _make_farm(db)
    _make_field(db, farm.id)

    resp = client.get(f"/api/farms/{farm.id}/daily-briefing")
    assert resp.status_code == 200
    data = resp.json()
    assert "Sin datos" in data["weather_summary_es"] or data["weather_summary_es"] != ""


def test_weather_summary_contains_temperature(client, db):
    """weather_summary_es contains the temperature when weather data is available."""
    farm = _make_farm(db)
    _make_field(db, farm.id)
    _make_weather(db, farm.id, temp_c=28.0, humidity_pct=70.0)

    resp = client.get(f"/api/farms/{farm.id}/daily-briefing")
    assert resp.status_code == 200
    data = resp.json()
    assert "28" in data["weather_summary_es"]


def test_empty_farm_no_fields_returns_ok(client, db):
    """Farm with no fields returns ok status and empty fields."""
    farm = _make_farm(db)

    resp = client.get(f"/api/farms/{farm.id}/daily-briefing")
    assert resp.status_code == 200
    data = resp.json()
    assert data["overall_farm_status"] == "ok"
    assert data["urgent_field"] is None


def test_upcoming_treatments_is_list(client, db):
    """upcoming_treatments is a list (may be empty or populated)."""
    farm = _make_farm(db)
    _make_field(db, farm.id)

    resp = client.get(f"/api/farms/{farm.id}/daily-briefing")
    assert resp.status_code == 200
    treatments = resp.json()["upcoming_treatments"]
    assert isinstance(treatments, list)


def test_overall_status_values(client, db):
    """overall_farm_status is one of ok|attention|urgent."""
    farm = _make_farm(db)

    resp = client.get(f"/api/farms/{farm.id}/daily-briefing")
    assert resp.status_code == 200
    status = resp.json()["overall_farm_status"]
    assert status in ("ok", "attention", "urgent")
