"""Tests for GET /api/farms/{farm_id}/fields/{field_id}/disease-risk-assessment."""

import pytest
from datetime import datetime

from cultivos.db.models import Farm, Field, WeatherRecord, NDVIResult, SoilAnalysis


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


def _make_weather(db, farm_id, humidity_pct=50.0, temp_c=25.0):
    w = WeatherRecord(
        farm_id=farm_id,
        temp_c=temp_c,
        humidity_pct=humidity_pct,
        wind_kmh=10.0,
        rainfall_mm=0.0,
        description="clear",
        forecast_3day=[],
    )
    db.add(w)
    db.commit()
    return w


def _make_ndvi(db, field_id, ndvi_mean=0.6):
    n = NDVIResult(
        field_id=field_id,
        ndvi_mean=ndvi_mean,
        ndvi_std=0.1,
        ndvi_min=0.3,
        ndvi_max=0.8,
        pixels_total=1000,
        stress_pct=10.0,
        zones=[],
    )
    db.add(n)
    db.commit()
    return n


def _make_soil(db, field_id, ph=6.5):
    s = SoilAnalysis(
        field_id=field_id,
        ph=ph,
        sampled_at=datetime(2026, 4, 1),
    )
    db.add(s)
    db.commit()
    return s


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_response_keys_present(client, db):
    """Response contains required schema keys."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/disease-risk-assessment")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "risk_level" in data
    assert "risk_score" in data
    assert "at_risk_diseases" in data
    assert "assessment_date" in data


def test_no_weather_data_returns_low_risk(client, db):
    """With no weather data, risk defaults to low (score < 26)."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/disease-risk-assessment")
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_level"] == "low"
    assert data["risk_score"] < 26


def test_high_humidity_increases_risk(client, db):
    """Humidity > 70% adds 20 points to risk score."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _make_weather(db, farm.id, humidity_pct=80.0, temp_c=25.0)

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/disease-risk-assessment")
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_score"] >= 20


def test_high_temperature_increases_risk(client, db):
    """Temperature > 35°C adds 10 points to risk score."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _make_weather(db, farm.id, humidity_pct=50.0, temp_c=38.0)

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/disease-risk-assessment")
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_score"] >= 10


def test_low_soil_ph_increases_risk(client, db):
    """Soil pH < 5.5 adds 15 points to risk score."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _make_weather(db, farm.id)
    _make_soil(db, field.id, ph=5.0)

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/disease-risk-assessment")
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_score"] >= 15


def test_multiple_factors_accumulate(client, db):
    """High humidity + high temp → score >= 30 (high risk level)."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _make_weather(db, farm.id, humidity_pct=80.0, temp_c=38.0)

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/disease-risk-assessment")
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_score"] >= 30  # 20 + 10


def test_at_risk_diseases_list_format(client, db):
    """at_risk_diseases entries contain name_es, probability, preventive_action."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _make_weather(db, farm.id, humidity_pct=80.0, temp_c=38.0)

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/disease-risk-assessment")
    assert resp.status_code == 200
    diseases = resp.json()["at_risk_diseases"]
    assert isinstance(diseases, list)
    if diseases:
        d = diseases[0]
        assert "name_es" in d
        assert "probability" in d
        assert "preventive_action" in d


def test_ndvi_drop_increases_risk(client, db):
    """NDVI drop > 20% month-over-month adds 25 points."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _make_weather(db, farm.id, humidity_pct=50.0, temp_c=25.0)
    # Older NDVI (higher), then newer (lower) — drop > 20%
    _make_ndvi(db, field.id, ndvi_mean=0.7)  # previous
    _make_ndvi(db, field.id, ndvi_mean=0.4)  # current — drop = (0.7-0.4)/0.7 ≈ 43%

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/disease-risk-assessment")
    assert resp.status_code == 200
    assert resp.json()["risk_score"] >= 25


def test_404_unknown_farm(client):
    """Unknown farm_id returns 404."""
    resp = client.get("/api/farms/99999/fields/1/disease-risk-assessment")
    assert resp.status_code == 404


def test_404_unknown_field(client, db):
    """Unknown field_id returns 404."""
    farm = _make_farm(db)
    resp = client.get(f"/api/farms/{farm.id}/fields/99999/disease-risk-assessment")
    assert resp.status_code == 404
