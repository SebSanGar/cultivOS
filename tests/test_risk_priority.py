"""Tests for GET /api/farms/{farm_id}/risk-priority endpoint.

Task #180: Risk-weighted field priority list.
priority_score = stress_score * min(days_since_treatment, 90) / 90
Sorted by priority_score DESC.
"""

from datetime import datetime, timedelta

import pytest

from cultivos.db.models import Farm, Field, TreatmentRecord


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_farm(db, name="Rancho Test"):
    farm = Farm(name=name, state="Jalisco", total_hectares=10.0)
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id, name="Campo Test", crop_type="maiz"):
    field = Field(farm_id=farm_id, name=name, crop_type=crop_type, hectares=5.0)
    db.add(field)
    db.commit()
    return field


def _add_treatment(db, field_id, days_ago=10):
    created_at = datetime.utcnow() - timedelta(days=days_ago)
    tr = TreatmentRecord(
        field_id=field_id,
        health_score_used=60.0,
        problema="plaga",
        causa_probable="insectos",
        tratamiento="compost",
        costo_estimado_mxn=500,
        urgencia="baja",
        prevencion="rotación",
        organic=True,
        created_at=created_at,
    )
    db.add(tr)
    db.commit()
    return tr


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_unknown_farm_returns_404(client):
    resp = client.get("/api/farms/99999/risk-priority")
    assert resp.status_code == 404


def test_farm_with_no_fields_returns_empty_list(client, db):
    farm = _make_farm(db)
    resp = client.get(f"/api/farms/{farm.id}/risk-priority")
    assert resp.status_code == 200
    assert resp.json() == []


def test_basic_response_structure(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_treatment(db, field.id, days_ago=10)

    resp = client.get(f"/api/farms/{farm.id}/risk-priority")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1

    item = data[0]
    assert "field_id" in item
    assert "crop_type" in item
    assert "stress_score" in item
    assert "days_since_treatment" in item
    assert "priority_score" in item
    assert "recommendation_es" in item


def test_no_treatment_history_treated_as_90_days(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    # No treatment records added

    resp = client.get(f"/api/farms/{farm.id}/risk-priority")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["days_since_treatment"] == 90


def test_priority_score_formula(client, db):
    """priority_score = stress_score * min(days, 90) / 90."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_treatment(db, field.id, days_ago=45)

    resp = client.get(f"/api/farms/{farm.id}/risk-priority")
    assert resp.status_code == 200
    item = resp.json()[0]

    expected = round(item["stress_score"] * 45 / 90, 2)
    assert abs(item["priority_score"] - expected) < 0.5


def test_days_capped_at_90(client, db):
    """days_since_treatment capped at 90 even if treatment is 120 days ago."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_treatment(db, field.id, days_ago=120)

    resp = client.get(f"/api/farms/{farm.id}/risk-priority")
    assert resp.status_code == 200
    item = resp.json()[0]
    assert item["days_since_treatment"] == 90


def test_sorted_by_priority_score_desc(client, db):
    farm = _make_farm(db)
    # Field A: recent treatment → lower priority factor
    field_a = _make_field(db, farm.id, name="Campo A")
    _add_treatment(db, field_a.id, days_ago=5)
    # Field B: old treatment → higher priority factor
    field_b = _make_field(db, farm.id, name="Campo B")
    _add_treatment(db, field_b.id, days_ago=80)

    resp = client.get(f"/api/farms/{farm.id}/risk-priority")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    # Should be sorted DESC by priority_score
    assert data[0]["priority_score"] >= data[1]["priority_score"]


def test_field_id_and_crop_type_correct(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id, crop_type="frijol")

    resp = client.get(f"/api/farms/{farm.id}/risk-priority")
    assert resp.status_code == 200
    item = resp.json()[0]
    assert item["field_id"] == field.id
    assert item["crop_type"] == "frijol"


def test_priority_score_bounded_0_to_100(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_treatment(db, field.id, days_ago=90)

    resp = client.get(f"/api/farms/{farm.id}/risk-priority")
    assert resp.status_code == 200
    item = resp.json()[0]
    assert 0.0 <= item["priority_score"] <= 100.0
    assert 0.0 <= item["stress_score"] <= 100.0
