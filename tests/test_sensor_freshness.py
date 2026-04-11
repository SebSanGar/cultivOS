"""Tests for GET /api/farms/{farm_id}/sensor-freshness

Shows per-field data staleness: days since last NDVI, soil, health score, and
(farm-level) weather record. Flags stale sensors (>14 days old).
"""

from datetime import datetime, timedelta

from cultivos.db.models import Farm, Field, HealthScore, NDVIResult, SoilAnalysis, WeatherRecord


# ── Helpers ────────────────────────────────────────────────────────────────────

def _farm(db):
    f = Farm(name="Finca Test", municipality="Guadalajara", total_hectares=10.0)
    db.add(f)
    db.commit()
    return f


def _field(db, farm_id, crop_type="maiz"):
    f = Field(farm_id=farm_id, name="Lote A", crop_type=crop_type, hectares=5.0)
    db.add(f)
    db.commit()
    return f


def _ndvi(db, field_id, days_ago):
    db.add(NDVIResult(
        field_id=field_id,
        ndvi_mean=0.6, ndvi_std=0.05, ndvi_min=0.4, ndvi_max=0.8,
        pixels_total=1000, stress_pct=5.0, zones=[],
        analyzed_at=datetime.utcnow() - timedelta(days=days_ago),
    ))
    db.commit()


def _soil(db, field_id, days_ago):
    db.add(SoilAnalysis(
        field_id=field_id,
        ph=6.5, organic_matter_pct=2.0,
        nitrogen_ppm=20, phosphorus_ppm=15, potassium_ppm=180,
        sampled_at=datetime.utcnow() - timedelta(days=days_ago),
        created_at=datetime.utcnow() - timedelta(days=days_ago),
    ))
    db.commit()


def _health(db, field_id, days_ago):
    db.add(HealthScore(
        field_id=field_id,
        score=78.0,
        scored_at=datetime.utcnow() - timedelta(days=days_ago),
    ))
    db.commit()


def _weather(db, farm_id, days_ago):
    db.add(WeatherRecord(
        farm_id=farm_id,
        temp_c=24.0, humidity_pct=55.0, wind_kmh=8.0,
        rainfall_mm=0.0, description="soleado",
        recorded_at=datetime.utcnow() - timedelta(days=days_ago),
    ))
    db.commit()


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_404_unknown_farm(client, db):
    r = client.get("/api/farms/99999/sensor-freshness")
    assert r.status_code == 404


def test_response_schema_keys(client, db):
    """Top-level response has all required keys."""
    farm = _farm(db)
    r = client.get(f"/api/farms/{farm.id}/sensor-freshness")
    assert r.status_code == 200
    data = r.json()
    assert "farm_id" in data
    assert "checked_at" in data
    assert "fields" in data


def test_field_item_schema_keys(client, db):
    """Each field entry has the required schema keys."""
    farm = _farm(db)
    field = _field(db, farm.id)
    r = client.get(f"/api/farms/{farm.id}/sensor-freshness")
    assert r.status_code == 200
    fields = r.json()["fields"]
    assert len(fields) == 1
    item = fields[0]
    assert "field_id" in item
    assert "crop_type" in item
    assert "ndvi_days_ago" in item
    assert "soil_days_ago" in item
    assert "health_days_ago" in item
    assert "weather_days_ago" in item
    assert "stale_sensors" in item


def test_fresh_data_has_empty_stale_sensors(client, db):
    """Field with all recent data → stale_sensors is empty."""
    farm = _farm(db)
    field = _field(db, farm.id)
    _ndvi(db, field.id, days_ago=1)
    _soil(db, field.id, days_ago=3)
    _health(db, field.id, days_ago=2)
    _weather(db, farm.id, days_ago=1)

    r = client.get(f"/api/farms/{farm.id}/sensor-freshness")
    assert r.status_code == 200
    item = r.json()["fields"][0]
    assert item["stale_sensors"] == []


def test_stale_ndvi_flagged(client, db):
    """NDVI older than 14 days → 'ndvi' in stale_sensors."""
    farm = _farm(db)
    field = _field(db, farm.id)
    _ndvi(db, field.id, days_ago=20)
    _health(db, field.id, days_ago=2)

    r = client.get(f"/api/farms/{farm.id}/sensor-freshness")
    assert r.status_code == 200
    item = r.json()["fields"][0]
    assert "ndvi" in item["stale_sensors"]


def test_stale_soil_flagged(client, db):
    """Soil analysis older than 14 days → 'soil' in stale_sensors."""
    farm = _farm(db)
    field = _field(db, farm.id)
    _soil(db, field.id, days_ago=20)

    r = client.get(f"/api/farms/{farm.id}/sensor-freshness")
    assert r.status_code == 200
    item = r.json()["fields"][0]
    assert "soil" in item["stale_sensors"]


def test_no_data_returns_null_days_ago(client, db):
    """Field with no sensor data → all days_ago values are null."""
    farm = _farm(db)
    field = _field(db, farm.id)

    r = client.get(f"/api/farms/{farm.id}/sensor-freshness")
    assert r.status_code == 200
    item = r.json()["fields"][0]
    assert item["ndvi_days_ago"] is None
    assert item["soil_days_ago"] is None
    assert item["health_days_ago"] is None
    assert item["weather_days_ago"] is None


def test_missing_data_is_stale(client, db):
    """Sensor with no records at all is treated as stale (in stale_sensors)."""
    farm = _farm(db)
    field = _field(db, farm.id)
    # NDVI has no record → should be flagged

    r = client.get(f"/api/farms/{farm.id}/sensor-freshness")
    assert r.status_code == 200
    item = r.json()["fields"][0]
    assert "ndvi" in item["stale_sensors"]


def test_days_ago_value_accuracy(client, db):
    """ndvi_days_ago is approximately correct (within 1 day tolerance)."""
    farm = _farm(db)
    field = _field(db, farm.id)
    _ndvi(db, field.id, days_ago=7)

    r = client.get(f"/api/farms/{farm.id}/sensor-freshness")
    assert r.status_code == 200
    item = r.json()["fields"][0]
    assert item["ndvi_days_ago"] is not None
    assert abs(item["ndvi_days_ago"] - 7) <= 1  # within 1 day tolerance


def test_farm_id_in_response(client, db):
    """farm_id in response matches the queried farm."""
    farm = _farm(db)
    r = client.get(f"/api/farms/{farm.id}/sensor-freshness")
    assert r.status_code == 200
    assert r.json()["farm_id"] == farm.id


def test_multiple_fields_all_returned(client, db):
    """Farm with 3 fields → 3 items in fields list."""
    farm = _farm(db)
    for i in range(3):
        _field(db, farm.id, crop_type=f"crop_{i}")

    r = client.get(f"/api/farms/{farm.id}/sensor-freshness")
    assert r.status_code == 200
    assert len(r.json()["fields"]) == 3
