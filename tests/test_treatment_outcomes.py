"""Tests for GET /api/knowledge/treatment-outcomes — per-crop treatment effectiveness."""

import pytest
from datetime import datetime, timedelta

from cultivos.db.models import Farm, Field, TreatmentRecord, HealthScore


def _make_farm(db):
    farm = Farm(name="Test Farm", state="Jalisco", total_hectares=10.0)
    db.add(farm)
    db.flush()
    return farm


def _make_field(db, farm_id, crop_type="maiz"):
    field = Field(farm_id=farm_id, name="Field 1", hectares=5.0, crop_type=crop_type)
    db.add(field)
    db.flush()
    return field


def _make_treatment(db, field_id, problema, health_score_used=50.0, created_at=None):
    if created_at is None:
        created_at = datetime(2026, 1, 10)
    t = TreatmentRecord(
        field_id=field_id,
        problema=problema,
        causa_probable="test cause",
        tratamiento="apply organic compost",
        costo_estimado_mxn=500,
        urgencia="media",
        prevencion="rotate crops",
        organic=True,
        health_score_used=health_score_used,
        created_at=created_at,
    )
    db.add(t)
    db.flush()
    return t


def _make_health_score(db, field_id, score, scored_at):
    h = HealthScore(
        field_id=field_id,
        score=score,
        sources=["test"],
        breakdown={},
        scored_at=scored_at,
        created_at=scored_at,
    )
    db.add(h)
    db.flush()
    return h


# --- Tests ---

def test_treatment_with_improved_health_positive_delta(client, db):
    """Treatment followed by higher health score → positive avg_health_delta."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id, crop_type="maiz")
    treatment_date = datetime(2026, 1, 10)
    _make_treatment(db, field.id, "plagas", health_score_used=50.0, created_at=treatment_date)
    # Health score 15 days after treatment
    _make_health_score(db, field.id, score=70.0, scored_at=treatment_date + timedelta(days=15))
    db.commit()

    resp = client.get("/api/knowledge/treatment-outcomes")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    item = data[0]
    assert item["crop_type"] == "maiz"
    assert item["treatment_summary"] == "plagas"
    assert item["avg_health_delta"] == pytest.approx(20.0)
    assert item["usage_count"] == 1


def test_treatment_with_no_followup_excluded_from_avg(client, db):
    """Treatment with no subsequent health score → excluded from avg_health_delta results."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id, crop_type="agave")
    treatment_date = datetime(2026, 1, 10)
    _make_treatment(db, field.id, "sequia", health_score_used=60.0, created_at=treatment_date)
    # No health score recorded after this treatment
    db.commit()

    resp = client.get("/api/knowledge/treatment-outcomes")
    assert resp.status_code == 200
    data = resp.json()
    # Should return empty (no treatments with followup data)
    assert data == []


def test_health_score_outside_30_day_window_excluded(client, db):
    """Health score more than 30 days after treatment → not counted as followup."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id, crop_type="frijol")
    treatment_date = datetime(2026, 1, 10)
    _make_treatment(db, field.id, "hongos", health_score_used=55.0, created_at=treatment_date)
    # Health score 45 days after — outside the 30-day window
    _make_health_score(db, field.id, score=75.0, scored_at=treatment_date + timedelta(days=45))
    db.commit()

    resp = client.get("/api/knowledge/treatment-outcomes")
    assert resp.status_code == 200
    data = resp.json()
    assert data == []


def test_crop_type_filter(client, db):
    """crop_type query param filters results to matching crop only."""
    farm = _make_farm(db)
    field_maiz = _make_field(db, farm.id, crop_type="maiz")
    field_agave = _make_field(db, farm.id, crop_type="agave")

    t_date = datetime(2026, 1, 10)
    _make_treatment(db, field_maiz.id, "plagas", health_score_used=50.0, created_at=t_date)
    _make_health_score(db, field_maiz.id, score=70.0, scored_at=t_date + timedelta(days=10))

    _make_treatment(db, field_agave.id, "sequia", health_score_used=40.0, created_at=t_date)
    _make_health_score(db, field_agave.id, score=60.0, scored_at=t_date + timedelta(days=10))
    db.commit()

    resp = client.get("/api/knowledge/treatment-outcomes?crop_type=maiz")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["crop_type"] == "maiz"


def test_sorted_by_avg_health_delta_desc(client, db):
    """Results sorted by avg_health_delta descending."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id, crop_type="maiz")

    t_date = datetime(2026, 1, 10)
    # Treatment 1: delta +30
    _make_treatment(db, field.id, "plagas", health_score_used=50.0, created_at=t_date)
    _make_health_score(db, field.id, score=80.0, scored_at=t_date + timedelta(days=5))

    # Treatment 2: delta +10
    t_date2 = datetime(2026, 2, 10)
    _make_treatment(db, field.id, "hongos", health_score_used=60.0, created_at=t_date2)
    _make_health_score(db, field.id, score=70.0, scored_at=t_date2 + timedelta(days=5))
    db.commit()

    resp = client.get("/api/knowledge/treatment-outcomes")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["avg_health_delta"] >= data[1]["avg_health_delta"]
    assert data[0]["treatment_summary"] == "plagas"


def test_date_range_filter_start_date(client, db):
    """start_date filters out treatments before the date."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id, crop_type="maiz")

    old_date = datetime(2025, 6, 1)
    new_date = datetime(2026, 1, 15)

    _make_treatment(db, field.id, "old_problem", health_score_used=50.0, created_at=old_date)
    _make_health_score(db, field.id, score=70.0, scored_at=old_date + timedelta(days=10))

    _make_treatment(db, field.id, "new_problem", health_score_used=55.0, created_at=new_date)
    _make_health_score(db, field.id, score=75.0, scored_at=new_date + timedelta(days=10))
    db.commit()

    resp = client.get("/api/knowledge/treatment-outcomes?start_date=2026-01-01")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["treatment_summary"] == "new_problem"


def test_empty_database_returns_empty_list(client, db):
    """No data in DB → empty list."""
    resp = client.get("/api/knowledge/treatment-outcomes")
    assert resp.status_code == 200
    assert resp.json() == []


def test_usage_count_aggregates_multiple_treatments(client, db):
    """Multiple treatments with same crop_type+problema → usage_count reflects total."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id, crop_type="maiz")

    for i in range(3):
        t_date = datetime(2026, 1, 10 + i * 5)
        _make_treatment(db, field.id, "plagas", health_score_used=50.0, created_at=t_date)
        _make_health_score(db, field.id, score=65.0, scored_at=t_date + timedelta(days=5))
    db.commit()

    resp = client.get("/api/knowledge/treatment-outcomes")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["usage_count"] == 3


def test_response_keys(client, db):
    """Response objects have all required keys."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id, crop_type="maiz")
    t_date = datetime(2026, 1, 10)
    _make_treatment(db, field.id, "plagas", health_score_used=50.0, created_at=t_date)
    _make_health_score(db, field.id, score=65.0, scored_at=t_date + timedelta(days=10))
    db.commit()

    resp = client.get("/api/knowledge/treatment-outcomes")
    assert resp.status_code == 200
    item = resp.json()[0]
    assert "crop_type" in item
    assert "treatment_summary" in item
    assert "avg_health_delta" in item
    assert "usage_count" in item
