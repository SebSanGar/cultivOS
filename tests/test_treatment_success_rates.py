"""Tests for GET /api/knowledge/treatment-success-rates."""

import pytest
from datetime import datetime, timedelta

from cultivos.db.models import Farm, Field, TreatmentRecord, HealthScore


def _make_farm(db):
    farm = Farm(name="Test Farm", state="Jalisco", total_hectares=10.0)
    db.add(farm)
    db.flush()
    return farm


def _make_field(db, farm_id, crop_type="maiz"):
    field = Field(farm_id=farm_id, name="F", hectares=5.0, crop_type=crop_type)
    db.add(field)
    db.flush()
    return field


def _make_treatment(db, field_id, problema, health_score_used=50.0, created_at=None):
    t = TreatmentRecord(
        field_id=field_id,
        problema=problema,
        causa_probable="c",
        tratamiento="organic compost",
        costo_estimado_mxn=500,
        urgencia="media",
        prevencion="rotate",
        organic=True,
        health_score_used=health_score_used,
        created_at=created_at or datetime(2026, 1, 10),
    )
    db.add(t)
    db.flush()
    return t


def _make_health(db, field_id, score, scored_at):
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


def test_all_positive_deltas_yield_100_success(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id, crop_type="maiz")
    for i in range(3):
        t_date = datetime(2026, 1, 10 + i * 5)
        _make_treatment(db, field.id, "plagas", health_score_used=50.0, created_at=t_date)
        _make_health(db, field.id, score=70.0, scored_at=t_date + timedelta(days=5))
    db.commit()

    resp = client.get("/api/knowledge/treatment-success-rates")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["crop_type"] == "maiz"
    assert data[0]["problema"] == "plagas"
    assert data[0]["treatment_count"] == 3
    assert data[0]["success_rate_pct"] == pytest.approx(100.0)
    assert data[0]["avg_health_delta"] == pytest.approx(20.0)


def test_mixed_delta_yields_partial_success(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id, crop_type="maiz")
    # 2 positive (delta +20), 2 negative (delta -10) = 50%
    t1 = datetime(2026, 1, 10)
    _make_treatment(db, field.id, "hongos", health_score_used=50.0, created_at=t1)
    _make_health(db, field.id, score=70.0, scored_at=t1 + timedelta(days=5))

    t2 = datetime(2026, 1, 20)
    _make_treatment(db, field.id, "hongos", health_score_used=50.0, created_at=t2)
    _make_health(db, field.id, score=70.0, scored_at=t2 + timedelta(days=5))

    t3 = datetime(2026, 2, 1)
    _make_treatment(db, field.id, "hongos", health_score_used=60.0, created_at=t3)
    _make_health(db, field.id, score=50.0, scored_at=t3 + timedelta(days=5))

    t4 = datetime(2026, 2, 10)
    _make_treatment(db, field.id, "hongos", health_score_used=60.0, created_at=t4)
    _make_health(db, field.id, score=50.0, scored_at=t4 + timedelta(days=5))
    db.commit()

    resp = client.get("/api/knowledge/treatment-success-rates")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["treatment_count"] == 4
    assert data[0]["success_rate_pct"] == pytest.approx(50.0)
    assert data[0]["avg_health_delta"] == pytest.approx(5.0)


def test_zero_delta_not_counted_as_success(client, db):
    """Zero delta = no improvement → does not count toward success_rate."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id, crop_type="frijol")
    t_date = datetime(2026, 1, 10)
    _make_treatment(db, field.id, "plagas", health_score_used=50.0, created_at=t_date)
    _make_health(db, field.id, score=50.0, scored_at=t_date + timedelta(days=5))
    db.commit()

    resp = client.get("/api/knowledge/treatment-success-rates")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["success_rate_pct"] == pytest.approx(0.0)


def test_sorted_by_success_rate_desc(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id, crop_type="maiz")

    # problem_a: 1/2 success (50%)
    t1 = datetime(2026, 1, 10)
    _make_treatment(db, field.id, "problem_a", health_score_used=50.0, created_at=t1)
    _make_health(db, field.id, score=70.0, scored_at=t1 + timedelta(days=5))
    t2 = datetime(2026, 1, 20)
    _make_treatment(db, field.id, "problem_a", health_score_used=60.0, created_at=t2)
    _make_health(db, field.id, score=40.0, scored_at=t2 + timedelta(days=5))

    # problem_b: 1/1 success (100%)
    t3 = datetime(2026, 2, 1)
    _make_treatment(db, field.id, "problem_b", health_score_used=50.0, created_at=t3)
    _make_health(db, field.id, score=80.0, scored_at=t3 + timedelta(days=5))
    db.commit()

    resp = client.get("/api/knowledge/treatment-success-rates")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["problema"] == "problem_b"
    assert data[0]["success_rate_pct"] == pytest.approx(100.0)
    assert data[1]["problema"] == "problem_a"
    assert data[1]["success_rate_pct"] == pytest.approx(50.0)


def test_crop_type_filter(client, db):
    farm = _make_farm(db)
    fm = _make_field(db, farm.id, crop_type="maiz")
    fa = _make_field(db, farm.id, crop_type="agave")
    t_date = datetime(2026, 1, 10)
    _make_treatment(db, fm.id, "plagas", health_score_used=50.0, created_at=t_date)
    _make_health(db, fm.id, score=70.0, scored_at=t_date + timedelta(days=5))
    _make_treatment(db, fa.id, "sequia", health_score_used=40.0, created_at=t_date)
    _make_health(db, fa.id, score=60.0, scored_at=t_date + timedelta(days=5))
    db.commit()

    resp = client.get("/api/knowledge/treatment-success-rates?crop_type=maiz")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["crop_type"] == "maiz"


def test_unknown_crop_returns_empty(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id, crop_type="maiz")
    t_date = datetime(2026, 1, 10)
    _make_treatment(db, field.id, "plagas", health_score_used=50.0, created_at=t_date)
    _make_health(db, field.id, score=70.0, scored_at=t_date + timedelta(days=5))
    db.commit()

    resp = client.get("/api/knowledge/treatment-success-rates?crop_type=nopal")
    assert resp.status_code == 200
    assert resp.json() == []


def test_no_treatments_returns_empty(client, db):
    resp = client.get("/api/knowledge/treatment-success-rates")
    assert resp.status_code == 200
    assert resp.json() == []


def test_treatment_without_followup_excluded(client, db):
    """Treatment with no HealthScore in 30-day window is not counted."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id, crop_type="maiz")
    t_date = datetime(2026, 1, 10)
    _make_treatment(db, field.id, "plagas", health_score_used=50.0, created_at=t_date)
    db.commit()

    resp = client.get("/api/knowledge/treatment-success-rates")
    assert resp.status_code == 200
    assert resp.json() == []


def test_response_keys(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id, crop_type="maiz")
    t_date = datetime(2026, 1, 10)
    _make_treatment(db, field.id, "plagas", health_score_used=50.0, created_at=t_date)
    _make_health(db, field.id, score=65.0, scored_at=t_date + timedelta(days=5))
    db.commit()

    resp = client.get("/api/knowledge/treatment-success-rates")
    assert resp.status_code == 200
    item = resp.json()[0]
    assert set(item.keys()) == {"crop_type", "problema", "avg_health_delta", "success_rate_pct", "treatment_count"}
