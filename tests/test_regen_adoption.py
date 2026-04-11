"""Tests for GET /api/cooperatives/{coop_id}/regen-adoption endpoint.

Task #176: Regen practice adoption rate per cooperative.
"""

from datetime import datetime, timedelta

import pytest

from cultivos.db.models import (
    Cooperative,
    Farm,
    Field,
    HealthScore,
    TreatmentRecord,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_coop(db, name="Cooperativa Test"):
    coop = Cooperative(name=name, state="Jalisco")
    db.add(coop)
    db.commit()
    return coop


def _make_farm(db, coop_id, name="Rancho Test"):
    farm = Farm(name=name, state="Jalisco", cooperative_id=coop_id, total_hectares=10.0)
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id, name="Campo Test"):
    field = Field(farm_id=farm_id, name=name, crop_type="maiz", hectares=5.0)
    db.add(field)
    db.commit()
    return field


def _add_health(db, field_id, score, days_ago=0):
    scored_at = datetime.utcnow() - timedelta(days=days_ago)
    hs = HealthScore(field_id=field_id, score=score, scored_at=scored_at)
    db.add(hs)
    db.commit()
    return hs


def _add_treatment(db, field_id, organic=True, days_ago=0):
    created_at = datetime.utcnow() - timedelta(days=days_ago)
    tr = TreatmentRecord(
        field_id=field_id,
        health_score_used=60.0,
        problema="plaga",
        causa_probable="insectos",
        tratamiento="compost orgánico",
        costo_estimado_mxn=500,
        urgencia="baja",
        prevencion="rotación de cultivos",
        organic=organic,
        created_at=created_at,
    )
    db.add(tr)
    db.commit()
    return tr


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_unknown_coop_returns_404(client):
    resp = client.get("/api/cooperatives/99999/regen-adoption")
    assert resp.status_code == 404


def test_empty_coop_no_farms(client, db):
    coop = _make_coop(db)
    resp = client.get(f"/api/cooperatives/{coop.id}/regen-adoption")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cooperative_id"] == coop.id
    assert data["farms"] == []
    assert data["overall_regen_score_avg"] == 0.0


def test_basic_response_structure(client, db):
    coop = _make_coop(db)
    farm = _make_farm(db, coop.id)
    field = _make_field(db, farm.id)
    _add_health(db, field.id, 80.0)
    _add_treatment(db, field.id, organic=True)

    resp = client.get(f"/api/cooperatives/{coop.id}/regen-adoption")
    assert resp.status_code == 200
    data = resp.json()

    assert "cooperative_id" in data
    assert "period_days" in data
    assert "overall_regen_score_avg" in data
    assert "farms" in data

    farm_entry = data["farms"][0]
    assert "farm_id" in farm_entry
    assert "farm_name" in farm_entry
    assert "regen_score" in farm_entry
    assert "treatment_count" in farm_entry


def test_period_days_echoed(client, db):
    coop = _make_coop(db)
    resp = client.get(f"/api/cooperatives/{coop.id}/regen-adoption?days=14")
    assert resp.status_code == 200
    assert resp.json()["period_days"] == 14


def test_default_days_is_30(client, db):
    coop = _make_coop(db)
    resp = client.get(f"/api/cooperatives/{coop.id}/regen-adoption")
    assert resp.status_code == 200
    assert resp.json()["period_days"] == 30


def test_treatment_count_in_period(client, db):
    coop = _make_coop(db)
    farm = _make_farm(db, coop.id)
    field = _make_field(db, farm.id)
    _add_health(db, field.id, 70.0)
    # 2 treatments within 30 days
    _add_treatment(db, field.id, organic=True, days_ago=5)
    _add_treatment(db, field.id, organic=False, days_ago=10)
    # 1 treatment outside the 30-day window
    _add_treatment(db, field.id, organic=True, days_ago=40)

    resp = client.get(f"/api/cooperatives/{coop.id}/regen-adoption?days=30")
    assert resp.status_code == 200
    data = resp.json()
    assert data["farms"][0]["treatment_count"] == 2


def test_no_data_farm_graceful_defaults(client, db):
    coop = _make_coop(db)
    _make_farm(db, coop.id)  # farm with no fields

    resp = client.get(f"/api/cooperatives/{coop.id}/regen-adoption")
    assert resp.status_code == 200
    data = resp.json()
    farm_entry = data["farms"][0]
    assert farm_entry["treatment_count"] == 0
    assert farm_entry["regen_score"] == 0.0


def test_three_farms_overall_avg(client, db):
    coop = _make_coop(db)
    regen_scores = []

    for i in range(3):
        farm = _make_farm(db, coop.id, name=f"Rancho {i}")
        field = _make_field(db, farm.id, name=f"Campo {i}")
        score = 60.0 + i * 10  # 60, 70, 80
        _add_health(db, field.id, score)
        _add_treatment(db, field.id, organic=True)
        # regen_score = (100% organic * 0.6) + (avg_health * 0.4) = 60 + score*0.4
        regen_scores.append(60.0 + score * 0.4)

    resp = client.get(f"/api/cooperatives/{coop.id}/regen-adoption")
    assert resp.status_code == 200
    data = resp.json()

    expected_avg = round(sum(regen_scores) / len(regen_scores), 2)
    assert abs(data["overall_regen_score_avg"] - expected_avg) < 1.0
    assert len(data["farms"]) == 3


def test_regen_score_nonzero_with_health_and_treatment(client, db):
    """Farm with health=80 + 100% organic treatments gets regen_score > 0."""
    coop = _make_coop(db)
    farm = _make_farm(db, coop.id)
    field = _make_field(db, farm.id)
    _add_health(db, field.id, 80.0)
    _add_treatment(db, field.id, organic=True)

    resp = client.get(f"/api/cooperatives/{coop.id}/regen-adoption")
    assert resp.status_code == 200
    data = resp.json()
    assert data["farms"][0]["regen_score"] > 0.0
    assert data["overall_regen_score_avg"] > 0.0
