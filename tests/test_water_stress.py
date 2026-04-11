"""Tests for GET /api/farms/{farm_id}/fields/{field_id}/water-stress."""

import pytest
from cultivos.db.models import Farm, Field, SoilAnalysis, ThermalResult, WeatherRecord
from datetime import datetime


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_farm(db, name="Rancho Prueba"):
    farm = Farm(name=name, state="Jalisco")
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id, name="Campo Uno", crop_type="maiz"):
    field = Field(farm_id=farm_id, name=name, crop_type=crop_type)
    db.add(field)
    db.commit()
    return field


def _make_soil(db, field_id, moisture_pct=45.0, ph=6.5):
    s = SoilAnalysis(
        field_id=field_id,
        ph=ph,
        moisture_pct=moisture_pct,
        sampled_at=datetime(2026, 4, 1),
    )
    db.add(s)
    db.commit()
    return s


def _make_thermal(db, field_id, stress_pct=10.0, irrigation_deficit=False):
    t = ThermalResult(
        field_id=field_id,
        temp_mean=28.0,
        temp_std=2.0,
        temp_min=24.0,
        temp_max=35.0,
        pixels_total=500,
        stress_pct=stress_pct,
        irrigation_deficit=irrigation_deficit,
    )
    db.add(t)
    db.commit()
    return t


def _make_weather(db, farm_id, temp_c=25.0):
    w = WeatherRecord(
        farm_id=farm_id,
        temp_c=temp_c,
        humidity_pct=50.0,
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
    field = _make_field(db, farm.id)

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/water-stress")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "urgency_level" in data
    assert "contributing_factors" in data
    assert "recommended_action_es" in data
    assert "next_check_hours" in data


def test_404_unknown_farm(client):
    """Unknown farm_id returns 404."""
    resp = client.get("/api/farms/99999/fields/1/water-stress")
    assert resp.status_code == 404


def test_404_unknown_field(client, db):
    """Unknown field_id returns 404."""
    farm = _make_farm(db)
    resp = client.get(f"/api/farms/{farm.id}/fields/99999/water-stress")
    assert resp.status_code == 404


def test_all_dry_signals_returns_severe(client, db):
    """Dry soil + high thermal stress + hot weather → severe urgency."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _make_soil(db, field.id, moisture_pct=15.0)   # < 20% → extreme
    _make_thermal(db, field.id, stress_pct=50.0)  # >= 40% → stressed
    _make_weather(db, farm.id, temp_c=38.0)       # > 35°C

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/water-stress")
    assert resp.status_code == 200
    assert resp.json()["urgency_level"] == "severe"


def test_all_normal_signals_returns_none(client, db):
    """Adequate moisture + no thermal stress + cool weather → none."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _make_soil(db, field.id, moisture_pct=60.0)   # > 30% → ok
    _make_thermal(db, field.id, stress_pct=5.0)   # < 40% → ok
    _make_weather(db, farm.id, temp_c=22.0)       # < 35°C → ok

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/water-stress")
    assert resp.status_code == 200
    assert resp.json()["urgency_level"] == "none"


def test_missing_soil_degrades_gracefully(client, db):
    """No soil data: endpoint still returns 200 (not 404) with thermal + weather only."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _make_thermal(db, field.id, stress_pct=50.0)
    _make_weather(db, farm.id, temp_c=38.0)

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/water-stress")
    assert resp.status_code == 200
    data = resp.json()
    assert data["urgency_level"] in ("none", "low", "moderate", "severe")


def test_thermal_stress_only_returns_low(client, db):
    """Only thermal irrigation deficit → at least low urgency."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _make_thermal(db, field.id, irrigation_deficit=True, stress_pct=10.0)

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/water-stress")
    assert resp.status_code == 200
    assert resp.json()["urgency_level"] in ("low", "moderate", "severe")


def test_urgency_level_valid_values(client, db):
    """urgency_level is one of none|low|moderate|severe."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/water-stress")
    assert resp.status_code == 200
    assert resp.json()["urgency_level"] in ("none", "low", "moderate", "severe")
