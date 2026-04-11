"""Tests for GET /api/farms/{farm_id}/active-alerts-summary

Composes WeatherRecord alerts + disease risk + water stress per field into:
{critical_count, high_count, top_action_es, next_check_date, safe}
"""

from datetime import datetime, timedelta

from cultivos.db.models import Farm, Field, SoilAnalysis, ThermalResult, WeatherRecord


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _farm(db, state="Jalisco"):
    f = Farm(name="Granja Test", municipality="Guadalajara", state=state, total_hectares=10.0)
    db.add(f)
    db.commit()
    return f


def _field(db, farm_id, crop_type="maiz"):
    f = Field(farm_id=farm_id, name="Lote A", crop_type=crop_type, hectares=5.0)
    db.add(f)
    db.commit()
    return f


def _weather_normal(db, farm_id):
    """Seed non-alerting weather data."""
    db.add(WeatherRecord(
        farm_id=farm_id,
        temp_c=22.0,
        humidity_pct=60.0,
        wind_kmh=10.0,
        rainfall_mm=5.0,
        description="soleado",
        forecast_3day=[],
        recorded_at=datetime.utcnow() - timedelta(hours=1),
    ))
    db.commit()


def _weather_extreme_heat(db, farm_id):
    """Seed extreme heat to trigger weather alert."""
    db.add(WeatherRecord(
        farm_id=farm_id,
        temp_c=42.0,
        humidity_pct=20.0,
        wind_kmh=10.0,
        rainfall_mm=0.0,
        description="muy caliente",
        forecast_3day=[],
        recorded_at=datetime.utcnow() - timedelta(hours=1),
    ))
    db.commit()


def _soil_low_moisture(db, field_id):
    """Seed very low soil moisture → severe water stress."""
    db.add(SoilAnalysis(
        field_id=field_id,
        moisture_pct=5.0,
        ph=6.5,
        organic_matter_pct=2.0,
        nitrogen_ppm=20.0,
        sampled_at=datetime.utcnow() - timedelta(hours=1),
    ))
    db.commit()


def _thermal_high_stress(db, field_id):
    """Seed high thermal stress → disease risk elevated."""
    db.add(ThermalResult(
        field_id=field_id,
        stress_pct=85.0,
        temp_mean=40.0, temp_std=3.0, temp_min=35.0, temp_max=44.0,
        pixels_total=1000,
        analyzed_at=datetime.utcnow() - timedelta(hours=1),
    ))
    db.commit()


# ── Tests ────────────────────────────────────────────────────────────────────────

def test_404_unknown_farm(client, db):
    r = client.get("/api/farms/99999/active-alerts-summary")
    assert r.status_code == 404


def test_response_schema_keys(client, db):
    """Response always has critical_count, high_count, top_action_es, next_check_date, safe."""
    farm = _farm(db)
    r = client.get(f"/api/farms/{farm.id}/active-alerts-summary")
    assert r.status_code == 200
    data = r.json()
    assert "critical_count" in data
    assert "high_count" in data
    assert "top_action_es" in data
    assert "next_check_date" in data
    assert "safe" in data


def test_no_fields_is_safe(client, db):
    """Farm with no fields → safe=True, counts=0."""
    farm = _farm(db)
    r = client.get(f"/api/farms/{farm.id}/active-alerts-summary")
    assert r.status_code == 200
    data = r.json()
    assert data["safe"] is True
    assert data["critical_count"] == 0
    assert data["high_count"] == 0


def test_no_stress_data_is_safe(client, db):
    """Farm with fields but no sensor data → safe=True (no signals)."""
    farm = _farm(db)
    _field(db, farm.id)
    _weather_normal(db, farm.id)
    r = client.get(f"/api/farms/{farm.id}/active-alerts-summary")
    assert r.status_code == 200
    data = r.json()
    assert data["safe"] is True


def test_severe_water_stress_counts_as_critical(client, db):
    """Field with severe water stress (low moisture + extreme heat) → critical_count >= 1, safe=False."""
    farm = _farm(db)
    field = _field(db, farm.id)
    _soil_low_moisture(db, field.id)
    # Add high temp weather to trigger soil_critical + temp_hot → "severe"
    db.add(WeatherRecord(
        farm_id=farm.id,
        temp_c=40.0,
        humidity_pct=15.0,
        wind_kmh=10.0,
        rainfall_mm=0.0,
        description="calor extremo",
        forecast_3day=[],
        recorded_at=datetime.utcnow() - timedelta(hours=1),
    ))
    db.commit()
    r = client.get(f"/api/farms/{farm.id}/active-alerts-summary")
    assert r.status_code == 200
    data = r.json()
    assert data["critical_count"] >= 1
    assert data["safe"] is False


def test_extreme_heat_weather_increments_count(client, db):
    """Extreme heat weather alert → counts incremented, safe=False."""
    farm = _farm(db)
    _field(db, farm.id)
    _weather_extreme_heat(db, farm.id)
    r = client.get(f"/api/farms/{farm.id}/active-alerts-summary")
    assert r.status_code == 200
    data = r.json()
    # critica or moderada heat → at least one count incremented
    assert data["critical_count"] + data["high_count"] >= 1
    assert data["safe"] is False


def test_top_action_es_is_string(client, db):
    """top_action_es is always a non-empty string."""
    farm = _farm(db)
    field = _field(db, farm.id)
    _soil_low_moisture(db, field.id)
    r = client.get(f"/api/farms/{farm.id}/active-alerts-summary")
    data = r.json()
    assert isinstance(data["top_action_es"], str)
    assert len(data["top_action_es"]) > 0


def test_next_check_date_is_isoformat(client, db):
    """next_check_date is a valid ISO date string."""
    farm = _farm(db)
    _field(db, farm.id)
    r = client.get(f"/api/farms/{farm.id}/active-alerts-summary")
    data = r.json()
    from datetime import date
    # Should not raise
    parsed = date.fromisoformat(data["next_check_date"])
    assert parsed >= date.today()


def test_critical_has_earlier_next_check_than_safe(client, db):
    """Critical farm gets an earlier next_check_date than a safe farm."""
    from datetime import date
    farm_safe = _farm(db)
    _field(db, farm_safe.id)
    r_safe = client.get(f"/api/farms/{farm_safe.id}/active-alerts-summary")
    safe_date = date.fromisoformat(r_safe.json()["next_check_date"])

    farm_critical = _farm(db)
    field_c = _field(db, farm_critical.id)
    _soil_low_moisture(db, field_c.id)
    r_crit = client.get(f"/api/farms/{farm_critical.id}/active-alerts-summary")
    crit_date = date.fromisoformat(r_crit.json()["next_check_date"])

    assert crit_date < safe_date
