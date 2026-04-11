"""Tests for farmer feedback trend endpoint — task #167."""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Farm, FarmerFeedback, Field, TreatmentRecord
from cultivos.db.session import get_db


def _make_treatment(db, field_id):
    tr = TreatmentRecord(
        field_id=field_id,
        health_score_used=60.0,
        problema="sequia",
        causa_probable="falta de agua",
        tratamiento="riego",
        costo_estimado_mxn=200,
        urgencia="media",
        prevencion="sistema de riego",
        organic=True,
    )
    db.add(tr)
    db.flush()
    return tr


def _make_feedback(db, field_id, treatment_id, rating, months_ago=0):
    created = datetime.utcnow() - timedelta(days=months_ago * 30)
    fb = FarmerFeedback(
        field_id=field_id,
        treatment_id=treatment_id,
        rating=rating,
        worked=True,
        created_at=created,
    )
    db.add(fb)
    return fb


@pytest.fixture()
def client(db):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


def test_404_unknown_farm(client):
    resp = client.get("/api/farms/9999/feedback-trend")
    assert resp.status_code == 404


def test_no_feedback_returns_empty(client, db):
    farm = Farm(name="Empty Farm", state="Jalisco")
    db.add(farm)
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/feedback-trend")
    assert resp.status_code == 200
    data = resp.json()
    assert data["farm_id"] == farm.id
    assert data["months"] == []
    assert "overall_trend" in data


def test_response_schema_keys(client, db):
    farm = Farm(name="Schema Farm", state="Jalisco")
    db.add(farm)
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/feedback-trend")
    assert resp.status_code == 200
    data = resp.json()
    assert "farm_id" in data
    assert "months" in data
    assert "overall_trend" in data


def test_monthly_grouping_correct(client, db):
    """Feedback from 2 different months shows correct count and avg per month."""
    farm = Farm(name="Trend Farm", state="Jalisco")
    field = Field(name="Parcela A", crop_type="maiz", hectares=5.0, farm=farm)
    db.add_all([farm, field])
    db.flush()

    tr = _make_treatment(db, field.id)

    # Month 0 (current): ratings 4, 5 → avg 4.5
    _make_feedback(db, field.id, tr.id, rating=4, months_ago=0)
    _make_feedback(db, field.id, tr.id, rating=5, months_ago=0)

    # Month 1 (1 month ago): rating 3 → avg 3.0
    _make_feedback(db, field.id, tr.id, rating=3, months_ago=1)

    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/feedback-trend")
    assert resp.status_code == 200
    data = resp.json()
    months = {m["month_label"]: m for m in data["months"]}

    # At least 2 distinct months
    assert len(months) >= 2

    # Find the month with 2 entries (current month)
    two_entry_months = [m for m in data["months"] if m["entry_count"] == 2]
    assert len(two_entry_months) == 1
    assert abs(two_entry_months[0]["avg_rating"] - 4.5) < 0.01


def test_month_item_schema_keys(client, db):
    farm = Farm(name="Schema2 Farm", state="Jalisco")
    field = Field(name="Parcela A", crop_type="maiz", hectares=5.0, farm=farm)
    db.add_all([farm, field])
    db.flush()

    tr = _make_treatment(db, field.id)
    _make_feedback(db, field.id, tr.id, rating=4, months_ago=0)
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/feedback-trend")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["months"]) >= 1
    item = data["months"][0]
    assert "month_label" in item
    assert "avg_rating" in item
    assert "entry_count" in item


def test_overall_trend_improving(client, db):
    """Recent months (last 2) avg rating noticeably higher than prior months → improving."""
    farm = Farm(name="Improve Farm", state="Jalisco")
    field = Field(name="Parcela A", crop_type="maiz", hectares=5.0, farm=farm)
    db.add_all([farm, field])
    db.flush()

    tr = _make_treatment(db, field.id)

    # Prior months (3-4 months ago): low ratings
    _make_feedback(db, field.id, tr.id, rating=2, months_ago=4)
    _make_feedback(db, field.id, tr.id, rating=2, months_ago=3)

    # Recent months (0-1 months ago): high ratings
    _make_feedback(db, field.id, tr.id, rating=5, months_ago=1)
    _make_feedback(db, field.id, tr.id, rating=5, months_ago=0)

    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/feedback-trend")
    assert resp.status_code == 200
    assert resp.json()["overall_trend"] == "improving"


def test_overall_trend_declining(client, db):
    """Recent months avg rating noticeably lower than prior months → declining."""
    farm = Farm(name="Decline Farm", state="Jalisco")
    field = Field(name="Parcela A", crop_type="maiz", hectares=5.0, farm=farm)
    db.add_all([farm, field])
    db.flush()

    tr = _make_treatment(db, field.id)

    # Prior months: high ratings
    _make_feedback(db, field.id, tr.id, rating=5, months_ago=4)
    _make_feedback(db, field.id, tr.id, rating=5, months_ago=3)

    # Recent months: low ratings
    _make_feedback(db, field.id, tr.id, rating=2, months_ago=1)
    _make_feedback(db, field.id, tr.id, rating=2, months_ago=0)

    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/feedback-trend")
    assert resp.status_code == 200
    assert resp.json()["overall_trend"] == "declining"


def test_overall_trend_stable(client, db):
    """Similar ratings across months → stable."""
    farm = Farm(name="Stable Farm", state="Jalisco")
    field = Field(name="Parcela A", crop_type="maiz", hectares=5.0, farm=farm)
    db.add_all([farm, field])
    db.flush()

    tr = _make_treatment(db, field.id)

    for months_ago in [4, 3, 1, 0]:
        _make_feedback(db, field.id, tr.id, rating=4, months_ago=months_ago)

    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/feedback-trend")
    assert resp.status_code == 200
    assert resp.json()["overall_trend"] == "stable"


def test_excludes_feedback_older_than_6_months(client, db):
    """Feedback older than 6 months is excluded from the trend."""
    farm = Farm(name="OldFeedback Farm", state="Jalisco")
    field = Field(name="Parcela A", crop_type="maiz", hectares=5.0, farm=farm)
    db.add_all([farm, field])
    db.flush()

    tr = _make_treatment(db, field.id)
    _make_feedback(db, field.id, tr.id, rating=1, months_ago=8)  # too old
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/feedback-trend")
    assert resp.status_code == 200
    assert resp.json()["months"] == []


def test_only_counts_this_farms_feedback(client, db):
    """Feedback from another farm's fields is not included."""
    farm_a = Farm(name="Farm A", state="Jalisco")
    farm_b = Farm(name="Farm B", state="Jalisco")
    field_a = Field(name="Campo A", crop_type="maiz", hectares=5.0, farm=farm_a)
    field_b = Field(name="Campo B", crop_type="maiz", hectares=5.0, farm=farm_b)
    db.add_all([farm_a, farm_b, field_a, field_b])
    db.flush()

    tr_b = _make_treatment(db, field_b.id)
    _make_feedback(db, field_b.id, tr_b.id, rating=2, months_ago=0)
    db.commit()

    resp = client.get(f"/api/farms/{farm_a.id}/feedback-trend")
    assert resp.status_code == 200
    assert resp.json()["months"] == []
