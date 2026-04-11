"""Tests for GET /api/farms/{farm_id}/field-comparison — multi-field side-by-side."""

import pytest
from datetime import datetime
from cultivos.db.models import Farm, Field, HealthScore, NDVIResult, SoilAnalysis


def _make_farm(db, name="Rancho Comparativo"):
    farm = Farm(name=name, state="Jalisco", total_hectares=30.0)
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id, name="Campo A", hectares=10.0, crop_type="maiz"):
    field = Field(farm_id=farm_id, name=name, hectares=hectares, crop_type=crop_type)
    db.add(field)
    db.commit()
    return field


def _add_health(db, field_id, score, trend="stable", scored_at=None):
    if scored_at is None:
        scored_at = datetime(2026, 3, 1)
    h = HealthScore(field_id=field_id, score=score, trend=trend, scored_at=scored_at)
    db.add(h)
    db.commit()
    return h


def _add_ndvi(db, field_id, ndvi_mean, analyzed_at=None):
    if analyzed_at is None:
        analyzed_at = datetime(2026, 3, 1)
    n = NDVIResult(
        field_id=field_id, ndvi_mean=ndvi_mean, ndvi_std=0.1,
        ndvi_min=0.2, ndvi_max=0.9, pixels_total=1000,
        stress_pct=10.0, zones=[], analyzed_at=analyzed_at,
    )
    db.add(n)
    db.commit()
    return n


def _add_soil(db, field_id, ph, sampled_at=None):
    if sampled_at is None:
        sampled_at = datetime(2026, 3, 1)
    s = SoilAnalysis(
        field_id=field_id, ph=ph, organic_matter_pct=2.0,
        nitrogen_ppm=30, phosphorus_ppm=20, potassium_ppm=150,
        texture="franco", moisture_pct=25, sampled_at=sampled_at,
    )
    db.add(s)
    db.commit()
    return s


# ── Tests ────────────────────────────────────────────────────────────────────

def test_404_unknown_farm(client):
    resp = client.get("/api/farms/99999/field-comparison")
    assert resp.status_code == 404


def test_response_keys(client, db):
    """Each item has all required keys."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_health(db, field.id, score=70.0, trend="improving")
    _add_ndvi(db, field.id, ndvi_mean=0.65)
    _add_soil(db, field.id, ph=6.5)

    resp = client.get(f"/api/farms/{farm.id}/field-comparison")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    item = items[0]
    for key in ("field_id", "field_name", "latest_health", "latest_ndvi", "latest_soil_ph", "trend"):
        assert key in item, f"Missing key: {key}"


def test_two_fields_sorted_by_health_desc(client, db):
    """Two fields sorted by latest_health descending."""
    farm = _make_farm(db)
    field1 = _make_field(db, farm.id, name="Good Field", hectares=5.0)
    field2 = _make_field(db, farm.id, name="Bad Field", hectares=5.0)
    _add_health(db, field1.id, score=85.0, trend="improving")
    _add_health(db, field2.id, score=45.0, trend="declining")

    resp = client.get(f"/api/farms/{farm.id}/field-comparison")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 2
    assert items[0]["latest_health"] == 85.0
    assert items[0]["field_name"] == "Good Field"
    assert items[1]["latest_health"] == 45.0


def test_field_with_no_data_returns_nulls(client, db):
    """Field with no health/NDVI/soil data returns null for those fields."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id, name="Empty Field")

    resp = client.get(f"/api/farms/{farm.id}/field-comparison")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    item = items[0]
    assert item["latest_health"] is None
    assert item["latest_ndvi"] is None
    assert item["latest_soil_ph"] is None
    assert item["trend"] is None


def test_mixed_fields_partial_data(client, db):
    """Farm with 2 fields — one full data, one no data."""
    farm = _make_farm(db)
    field1 = _make_field(db, farm.id, name="Full Data")
    field2 = _make_field(db, farm.id, name="No Data")

    _add_health(db, field1.id, score=75.0, trend="stable")
    _add_ndvi(db, field1.id, ndvi_mean=0.60)
    _add_soil(db, field1.id, ph=6.8)

    resp = client.get(f"/api/farms/{farm.id}/field-comparison")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 2
    by_name = {i["field_name"]: i for i in items}
    full = by_name["Full Data"]
    empty = by_name["No Data"]
    assert full["latest_health"] == 75.0
    assert full["latest_ndvi"] == pytest.approx(0.60)
    assert full["latest_soil_ph"] == pytest.approx(6.8)
    assert full["trend"] == "stable"
    assert empty["latest_health"] is None


def test_uses_latest_values_when_multiple_records(client, db):
    """Field with multiple health/NDVI/soil records → latest used."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    _add_health(db, field.id, score=50.0, scored_at=datetime(2025, 12, 1))
    _add_health(db, field.id, score=80.0, scored_at=datetime(2026, 3, 1))  # latest
    _add_ndvi(db, field.id, ndvi_mean=0.40, analyzed_at=datetime(2025, 12, 1))
    _add_ndvi(db, field.id, ndvi_mean=0.72, analyzed_at=datetime(2026, 3, 1))  # latest
    _add_soil(db, field.id, ph=5.5, sampled_at=datetime(2025, 12, 1))
    _add_soil(db, field.id, ph=6.5, sampled_at=datetime(2026, 3, 1))  # latest

    resp = client.get(f"/api/farms/{farm.id}/field-comparison")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    item = items[0]
    assert item["latest_health"] == 80.0
    assert item["latest_ndvi"] == pytest.approx(0.72)
    assert item["latest_soil_ph"] == pytest.approx(6.5)


def test_empty_farm_returns_empty_list(client, db):
    """Farm with no fields → empty list."""
    farm = _make_farm(db)
    resp = client.get(f"/api/farms/{farm.id}/field-comparison")
    assert resp.status_code == 200
    assert resp.json() == []


def test_farm_id_correct_in_response(client, db):
    """field_id in response matches the actual field."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id, name="Unique")
    _add_health(db, field.id, score=60.0)

    resp = client.get(f"/api/farms/{farm.id}/field-comparison")
    assert resp.status_code == 200
    item = resp.json()[0]
    assert item["field_id"] == field.id
    assert item["field_name"] == "Unique"
