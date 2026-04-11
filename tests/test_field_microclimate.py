"""Tests for GET /api/farms/{farm_id}/fields/{field_id}/microclimate endpoint."""

import pytest
from datetime import datetime, timedelta
from cultivos.db.models import Farm, Field, WeatherRecord


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_farm(db, name="Rancho Test"):
    farm = Farm(name=name, state="Jalisco", total_hectares=10.0)
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id, name="Campo Test"):
    field = Field(farm_id=farm_id, name=name, crop_type="maiz", hectares=5.0)
    db.add(field)
    db.commit()
    return field


def _add_weather(db, farm_id, temp_c, humidity_pct=60.0, wind_kmh=10.0, rainfall_mm=0.0, days_ago=0):
    record = WeatherRecord(
        farm_id=farm_id,
        temp_c=temp_c,
        humidity_pct=humidity_pct,
        wind_kmh=wind_kmh,
        rainfall_mm=rainfall_mm,
        description="Test weather",
        recorded_at=datetime.utcnow() - timedelta(days=days_ago),
    )
    db.add(record)
    db.commit()
    return record


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_404_unknown_field(client, db):
    farm = _make_farm(db)
    r = client.get(f"/api/farms/{farm.id}/fields/9999/microclimate")
    assert r.status_code == 404


def test_404_unknown_farm(client, db):
    r = client.get("/api/farms/9999/fields/1/microclimate")
    assert r.status_code == 404


def test_aggregates_7_days_correctly(client, db):
    """7 days of weather → correct avg/max/min/total/avg_humidity."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    _add_weather(db, farm.id, temp_c=20.0, humidity_pct=50.0, wind_kmh=5.0, rainfall_mm=2.0, days_ago=0)
    _add_weather(db, farm.id, temp_c=25.0, humidity_pct=60.0, wind_kmh=15.0, rainfall_mm=5.0, days_ago=2)
    _add_weather(db, farm.id, temp_c=15.0, humidity_pct=70.0, wind_kmh=10.0, rainfall_mm=0.0, days_ago=5)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/microclimate")
    assert r.status_code == 200
    data = r.json()

    assert data["field_id"] == field.id
    assert data["period_days"] == 7
    assert data["avg_temp_c"] == pytest.approx(20.0, abs=0.5)
    assert data["max_temp_c"] == pytest.approx(25.0, abs=0.1)
    assert data["min_temp_c"] == pytest.approx(15.0, abs=0.1)
    assert data["total_rainfall_mm"] == pytest.approx(7.0, abs=0.1)
    assert data["avg_humidity_pct"] == pytest.approx(60.0, abs=1.0)


def test_frost_risk_detected(client, db):
    """Records with temp_c < 4.0 count as frost_risk_days."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    _add_weather(db, farm.id, temp_c=2.0, days_ago=0)   # frost
    _add_weather(db, farm.id, temp_c=3.5, days_ago=1)   # frost
    _add_weather(db, farm.id, temp_c=10.0, days_ago=2)  # no frost

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/microclimate")
    assert r.status_code == 200
    assert r.json()["frost_risk_days"] == 2


def test_excludes_records_older_than_7_days(client, db):
    """Records from 8+ days ago should not be included."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    _add_weather(db, farm.id, temp_c=30.0, days_ago=8)  # outside window
    _add_weather(db, farm.id, temp_c=20.0, days_ago=1)  # inside window

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/microclimate")
    assert r.status_code == 200
    data = r.json()
    assert data["max_temp_c"] == pytest.approx(20.0, abs=0.1)  # not 30.0


def test_no_weather_data_graceful(client, db):
    """Field with no weather records returns graceful empty response."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/microclimate")
    assert r.status_code == 200
    data = r.json()
    assert data["field_id"] == field.id
    assert data["avg_temp_c"] is None
    assert data["frost_risk_days"] == 0


def test_response_schema_fields(client, db):
    """Response has all required schema fields."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_weather(db, farm.id, temp_c=22.0)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/microclimate")
    assert r.status_code == 200
    data = r.json()
    for key in ("field_id", "period_days", "avg_temp_c", "max_temp_c", "min_temp_c",
                "total_rainfall_mm", "avg_humidity_pct", "frost_risk_days", "summary_es"):
        assert key in data, f"Missing key: {key}"


def test_summary_es_present(client, db):
    """summary_es is a non-empty Spanish string."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_weather(db, farm.id, temp_c=18.0, rainfall_mm=3.0)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/microclimate")
    assert r.status_code == 200
    assert isinstance(r.json()["summary_es"], str)
    assert len(r.json()["summary_es"]) > 5
