"""Tests for GET /api/farms/{farm_id}/fields/{field_id}/soil-trajectory endpoint."""

import pytest
from datetime import datetime, timedelta

from cultivos.db.models import Farm, Field, SoilAnalysis


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


def _add_soil(db, field_id, ph, organic_matter_pct, months_ago=0):
    """Add a SoilAnalysis record N months ago from now."""
    sampled_at = datetime.utcnow() - timedelta(days=months_ago * 30)
    sa = SoilAnalysis(
        field_id=field_id,
        ph=ph,
        organic_matter_pct=organic_matter_pct,
        sampled_at=sampled_at,
    )
    db.add(sa)
    db.commit()
    return sa


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_404_unknown_farm(client, db):
    r = client.get("/api/farms/99999/fields/99999/soil-trajectory")
    assert r.status_code == 404


def test_404_unknown_field(client, db):
    farm = _make_farm(db)
    r = client.get(f"/api/farms/{farm.id}/fields/99999/soil-trajectory")
    assert r.status_code == 404


def test_no_soil_data_returns_empty(client, db):
    """Field with no SoilAnalysis → empty months list, stable trends."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/soil-trajectory")
    assert r.status_code == 200
    data = r.json()
    assert data["field_id"] == field.id
    assert data["months"] == []
    assert data["ph_trend"] == "stable"
    assert data["organic_matter_trend"] == "stable"


def test_response_schema_keys(client, db):
    """Response contains all required schema fields."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_soil(db, field.id, ph=6.5, organic_matter_pct=3.0, months_ago=1)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/soil-trajectory")
    assert r.status_code == 200
    data = r.json()
    assert "field_id" in data
    assert "months" in data
    assert "ph_trend" in data
    assert "organic_matter_trend" in data
    month = data["months"][0]
    assert "month_label" in month
    assert "avg_ph" in month
    assert "avg_organic_matter_pct" in month


def test_three_months_correct_values(client, db):
    """3 months of data → correct month labels and averaged values."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    # Two records in the same month (1 month ago) → should be averaged
    _add_soil(db, field.id, ph=6.0, organic_matter_pct=2.0, months_ago=2)
    _add_soil(db, field.id, ph=6.5, organic_matter_pct=3.0, months_ago=1)
    _add_soil(db, field.id, ph=7.0, organic_matter_pct=4.0, months_ago=0)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/soil-trajectory")
    assert r.status_code == 200
    data = r.json()
    # Should have 3 months
    assert len(data["months"]) == 3
    # Months should be sorted oldest → newest
    phs = [m["avg_ph"] for m in data["months"]]
    assert phs == sorted(phs)


def test_ph_trend_improving(client, db):
    """pH increasing last 2 months vs prior 2 months → ph_trend=improving."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_soil(db, field.id, ph=5.5, organic_matter_pct=2.0, months_ago=4)
    _add_soil(db, field.id, ph=5.8, organic_matter_pct=2.0, months_ago=3)
    _add_soil(db, field.id, ph=6.5, organic_matter_pct=2.0, months_ago=1)
    _add_soil(db, field.id, ph=6.8, organic_matter_pct=2.0, months_ago=0)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/soil-trajectory")
    assert r.status_code == 200
    assert r.json()["ph_trend"] == "improving"


def test_organic_matter_trend_declining(client, db):
    """Organic matter decreasing last 2 months vs prior 2 → organic_matter_trend=declining."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_soil(db, field.id, ph=6.5, organic_matter_pct=4.0, months_ago=4)
    _add_soil(db, field.id, ph=6.5, organic_matter_pct=3.8, months_ago=3)
    _add_soil(db, field.id, ph=6.5, organic_matter_pct=2.5, months_ago=1)
    _add_soil(db, field.id, ph=6.5, organic_matter_pct=2.2, months_ago=0)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/soil-trajectory")
    assert r.status_code == 200
    assert r.json()["organic_matter_trend"] == "declining"


def test_single_month_trend_stable(client, db):
    """Only one month of data → both trends are stable."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_soil(db, field.id, ph=6.5, organic_matter_pct=3.0, months_ago=0)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/soil-trajectory")
    assert r.status_code == 200
    data = r.json()
    assert data["ph_trend"] == "stable"
    assert data["organic_matter_trend"] == "stable"


def test_excludes_records_older_than_6_months(client, db):
    """Records older than 6 months are excluded from the trajectory."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_soil(db, field.id, ph=5.0, organic_matter_pct=1.0, months_ago=8)  # excluded
    _add_soil(db, field.id, ph=6.5, organic_matter_pct=3.0, months_ago=1)  # included

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/soil-trajectory")
    assert r.status_code == 200
    data = r.json()
    # Only 1 month in window
    assert len(data["months"]) == 1
    assert data["months"][0]["avg_ph"] == pytest.approx(6.5, abs=0.1)
