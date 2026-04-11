"""Tests for GET /api/farms/{farm_id}/fields/{field_id}/resilience-score."""

import pytest
from datetime import datetime

from cultivos.db.models import Farm, Field, HealthScore, SoilAnalysis, WeatherRecord


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


def _make_soil(db, field_id, ph=6.5, moisture_pct=45.0):
    s = SoilAnalysis(
        field_id=field_id,
        ph=ph,
        moisture_pct=moisture_pct,
        sampled_at=datetime(2026, 4, 1),
    )
    db.add(s)
    db.commit()
    return s


def _make_weather(db, farm_id, temp_c=25.0, humidity_pct=50.0):
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
    field = _make_field(db, farm.id)

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/resilience-score")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "field_id" in data
    assert "resilience_score" in data
    assert "components" in data
    assert "interpretation_es" in data


def test_components_keys_present(client, db):
    """Components dict contains health, soil_ph, water_stress, disease_risk."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/resilience-score")
    assert resp.status_code == 200
    components = resp.json()["components"]
    assert "health" in components
    assert "soil_ph" in components
    assert "water_stress" in components
    assert "disease_risk" in components


def test_404_unknown_farm(client):
    """Unknown farm_id returns 404."""
    resp = client.get("/api/farms/99999/fields/1/resilience-score")
    assert resp.status_code == 404


def test_404_unknown_field(client, db):
    """Unknown field_id (field not in farm) returns 404."""
    farm = _make_farm(db)
    resp = client.get(f"/api/farms/{farm.id}/fields/99999/resilience-score")
    assert resp.status_code == 404


def test_score_range_is_valid(client, db):
    """resilience_score is between 0 and 100."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _make_health(db, field.id, score=80.0)
    _make_soil(db, field.id, ph=6.5)
    _make_weather(db, farm.id)

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/resilience-score")
    assert resp.status_code == 200
    score = resp.json()["resilience_score"]
    assert 0 <= score <= 100


def test_high_health_good_soil_yields_high_score(client, db):
    """Healthy field + optimal soil + no stress → resilience_score >= 70."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _make_health(db, field.id, score=90.0)
    _make_soil(db, field.id, ph=6.5)       # optimal pH
    _make_weather(db, farm.id, temp_c=24.0, humidity_pct=50.0)  # benign weather

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/resilience-score")
    assert resp.status_code == 200
    assert resp.json()["resilience_score"] >= 70


def test_poor_health_bad_soil_yields_low_score(client, db):
    """Sick field + acidic soil + hot humid weather → resilience_score <= 50."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _make_health(db, field.id, score=20.0)
    _make_soil(db, field.id, ph=4.5, moisture_pct=10.0)   # very acidic + dry
    _make_weather(db, farm.id, temp_c=38.0, humidity_pct=80.0)  # hot + humid

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/resilience-score")
    assert resp.status_code == 200
    assert resp.json()["resilience_score"] <= 50


def test_missing_all_data_returns_neutral_score(client, db):
    """No sensor data at all → neutral score (around 50) — graceful degradation."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    # No health, soil, or weather records

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/resilience-score")
    assert resp.status_code == 200
    score = resp.json()["resilience_score"]
    assert 30 <= score <= 70  # neutral range when no data


def test_interpretation_es_is_string(client, db):
    """interpretation_es is a non-empty string."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/resilience-score")
    assert resp.status_code == 200
    interp = resp.json()["interpretation_es"]
    assert isinstance(interp, str)
    assert len(interp) > 0


def test_field_id_matches_request(client, db):
    """field_id in response matches the requested field."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/resilience-score")
    assert resp.status_code == 200
    assert resp.json()["field_id"] == field.id
