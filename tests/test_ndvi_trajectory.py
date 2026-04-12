"""Tests for GET /api/farms/{farm_id}/fields/{field_id}/ndvi-trajectory endpoint."""

import pytest
from datetime import datetime, timedelta

from cultivos.db.models import Farm, Field, NDVIResult


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_farm(db):
    farm = Farm(name="Test Farm", municipality="Guadalajara", total_hectares=10.0)
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id):
    field = Field(farm_id=farm_id, name="Lote A", crop_type="maiz", hectares=5.0)
    db.add(field)
    db.commit()
    return field


def _add_ndvi(db, field_id, ndvi_mean, stress_pct, months_ago=0):
    """Add an NDVIResult record roughly N months ago from now."""
    analyzed_at = datetime.utcnow() - timedelta(days=months_ago * 30)
    result = NDVIResult(
        field_id=field_id,
        ndvi_mean=ndvi_mean,
        ndvi_std=0.05,
        ndvi_min=max(0.0, ndvi_mean - 0.2),
        ndvi_max=min(1.0, ndvi_mean + 0.2),
        pixels_total=10000,
        stress_pct=stress_pct,
        zones=[],
        analyzed_at=analyzed_at,
    )
    db.add(result)
    db.commit()
    return result


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_404_unknown_farm(client, db):
    r = client.get("/api/farms/99999/fields/99999/ndvi-trajectory")
    assert r.status_code == 404


def test_404_unknown_field(client, db):
    farm = _make_farm(db)
    r = client.get(f"/api/farms/{farm.id}/fields/99999/ndvi-trajectory")
    assert r.status_code == 404


def test_no_ndvi_data_returns_empty(client, db):
    """Field with no NDVIResult → empty months list, stable trends."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/ndvi-trajectory")
    assert r.status_code == 200
    data = r.json()
    assert data["field_id"] == field.id
    assert data["months"] == []
    assert data["ndvi_trend"] == "stable"
    assert data["stress_trend"] == "stable"


def test_response_schema_keys(client, db):
    """Response contains all required schema fields."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_ndvi(db, field.id, ndvi_mean=0.6, stress_pct=15.0, months_ago=1)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/ndvi-trajectory")
    assert r.status_code == 200
    data = r.json()
    assert "field_id" in data
    assert "months" in data
    assert "ndvi_trend" in data
    assert "stress_trend" in data
    month = data["months"][0]
    assert "month_label" in month
    assert "avg_ndvi" in month
    assert "avg_stress_pct" in month


def test_three_months_sorted_oldest_to_newest(client, db):
    """3 months of data → labels sorted oldest to newest."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_ndvi(db, field.id, ndvi_mean=0.50, stress_pct=30.0, months_ago=2)
    _add_ndvi(db, field.id, ndvi_mean=0.60, stress_pct=20.0, months_ago=1)
    _add_ndvi(db, field.id, ndvi_mean=0.70, stress_pct=10.0, months_ago=0)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/ndvi-trajectory")
    assert r.status_code == 200
    data = r.json()
    assert len(data["months"]) == 3
    labels = [m["month_label"] for m in data["months"]]
    assert labels == sorted(labels)


def test_ndvi_trend_improving(client, db):
    """NDVI increasing last 2 months vs prior 2 → ndvi_trend=improving."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_ndvi(db, field.id, ndvi_mean=0.50, stress_pct=30.0, months_ago=3)
    _add_ndvi(db, field.id, ndvi_mean=0.52, stress_pct=28.0, months_ago=2)
    _add_ndvi(db, field.id, ndvi_mean=0.65, stress_pct=15.0, months_ago=1)
    _add_ndvi(db, field.id, ndvi_mean=0.70, stress_pct=10.0, months_ago=0)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/ndvi-trajectory")
    assert r.status_code == 200
    assert r.json()["ndvi_trend"] == "improving"


def test_stress_trend_improving_when_stress_decreasing(client, db):
    """Stress% decreasing last 2 months vs prior 2 → stress_trend=improving (lower stress is better)."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_ndvi(db, field.id, ndvi_mean=0.60, stress_pct=40.0, months_ago=3)
    _add_ndvi(db, field.id, ndvi_mean=0.60, stress_pct=38.0, months_ago=2)
    _add_ndvi(db, field.id, ndvi_mean=0.60, stress_pct=20.0, months_ago=1)
    _add_ndvi(db, field.id, ndvi_mean=0.60, stress_pct=15.0, months_ago=0)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/ndvi-trajectory")
    assert r.status_code == 200
    assert r.json()["stress_trend"] == "improving"


def test_single_month_trend_stable(client, db):
    """Only one month of data → both trends are stable."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_ndvi(db, field.id, ndvi_mean=0.65, stress_pct=15.0, months_ago=0)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/ndvi-trajectory")
    assert r.status_code == 200
    data = r.json()
    assert data["ndvi_trend"] == "stable"
    assert data["stress_trend"] == "stable"


def test_excludes_records_older_than_90_days(client, db):
    """Records older than 90 days are excluded from the trajectory."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_ndvi(db, field.id, ndvi_mean=0.30, stress_pct=70.0, months_ago=5)  # excluded
    _add_ndvi(db, field.id, ndvi_mean=0.65, stress_pct=15.0, months_ago=1)  # included

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/ndvi-trajectory")
    assert r.status_code == 200
    data = r.json()
    assert len(data["months"]) == 1
    assert data["months"][0]["avg_ndvi"] == pytest.approx(0.65, abs=0.01)
    assert data["months"][0]["avg_stress_pct"] == pytest.approx(15.0, abs=0.1)


def test_averages_multiple_records_within_same_month(client, db):
    """Two records in same month → averaged to a single bucket."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_ndvi(db, field.id, ndvi_mean=0.60, stress_pct=20.0, months_ago=0)
    _add_ndvi(db, field.id, ndvi_mean=0.80, stress_pct=10.0, months_ago=0)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/ndvi-trajectory")
    assert r.status_code == 200
    data = r.json()
    assert len(data["months"]) == 1
    assert data["months"][0]["avg_ndvi"] == pytest.approx(0.70, abs=0.01)
    assert data["months"][0]["avg_stress_pct"] == pytest.approx(15.0, abs=0.1)
