"""Tests for cooperative monthly progress snapshot.

GET /api/cooperatives/{coop_id}/monthly-progress?months=6
Per-month avg_health, total_treatments, new_observations, regen_score_avg.
Overall trend (improving|stable|declining) via last-half vs first-half regen delta.
"""

from datetime import datetime

import pytest

from cultivos.db.models import (
    Cooperative,
    Farm,
    FarmerObservation,
    Field,
    HealthScore,
    TreatmentRecord,
)


@pytest.fixture
def coop(db):
    c = Cooperative(name="Cooperativa Progreso", state="Jalisco")
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def _farm(db, coop, name="Rancho"):
    f = Farm(
        name=name,
        owner_name="Test",
        state="Jalisco",
        total_hectares=50.0,
        cooperative_id=coop.id,
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def _field(db, farm, name="Parcela"):
    fld = Field(farm_id=farm.id, name=name, crop_type="maiz", hectares=5.0)
    db.add(fld)
    db.commit()
    db.refresh(fld)
    return fld


def _health(db, field, score, when):
    db.add(HealthScore(field_id=field.id, score=score, sources=["ndvi"],
                       breakdown={}, scored_at=when))
    db.commit()


def _treatment(db, field, organic, when):
    t = TreatmentRecord(
        field_id=field.id,
        health_score_used=70.0,
        problema="plaga",
        causa_probable="humedad",
        tratamiento="neem",
        urgencia="baja",
        prevencion="rotacion",
        organic=organic,
    )
    t.created_at = when
    db.add(t)
    db.commit()


def _obs(db, field, when):
    o = FarmerObservation(
        field_id=field.id,
        observation_es="riego ok",
        observation_type="neutral",
    )
    o.created_at = when
    db.add(o)
    db.commit()


def test_monthly_progress_basic(client, db, coop):
    """One farm, two months of data — endpoint returns 2 entries."""
    f = _farm(db, coop)
    fld = _field(db, f)
    m1 = datetime(2026, 1, 15)
    m2 = datetime(2026, 2, 15)
    _health(db, fld, 70.0, m1)
    _health(db, fld, 80.0, m2)
    _treatment(db, fld, True, m1)
    _treatment(db, fld, True, m2)
    _treatment(db, fld, False, m2)
    _obs(db, fld, m1)
    _obs(db, fld, m2)
    _obs(db, fld, m2)

    resp = client.get(f"/api/cooperatives/{coop.id}/monthly-progress?months=12")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cooperative_id"] == coop.id
    months = {m["month"]: m for m in data["months"]}
    assert "2026-01" in months
    assert "2026-02" in months
    jan = months["2026-01"]
    assert jan["avg_health"] == pytest.approx(70.0, abs=0.1)
    assert jan["total_treatments"] == 1
    assert jan["new_observations"] == 1
    # organic_pct=100, avg_health=70 → 100*0.6 + 70*0.4 = 88.0
    assert jan["regen_score_avg"] == pytest.approx(88.0, abs=0.1)
    feb = months["2026-02"]
    assert feb["total_treatments"] == 2
    assert feb["new_observations"] == 2
    # organic 1/2 = 50%, avg_health=80 → 50*0.6 + 80*0.4 = 62.0
    assert feb["regen_score_avg"] == pytest.approx(62.0, abs=0.1)


def test_monthly_progress_trend_improving(client, db, coop):
    """Regen score grows from ~30 to ~90 over 6 months → improving."""
    f = _farm(db, coop)
    fld = _field(db, f)
    # 6 months, regen_score increasing steadily (via organic_pct + health)
    base = [(2026, m) for m in range(1, 7)]
    healths = [30, 40, 50, 70, 80, 90]
    organics = [False, False, False, True, True, True]
    for (y, m), h, org in zip(base, healths, organics):
        when = datetime(y, m, 15)
        _health(db, fld, float(h), when)
        _treatment(db, fld, org, when)

    resp = client.get(f"/api/cooperatives/{coop.id}/monthly-progress?months=12")
    data = resp.json()
    assert data["overall_trend"] == "improving"
    assert len(data["months"]) == 6


def test_monthly_progress_trend_declining(client, db, coop):
    """Regen score shrinks over 6 months → declining."""
    f = _farm(db, coop)
    fld = _field(db, f)
    base = [(2026, m) for m in range(1, 7)]
    healths = [90, 80, 70, 50, 40, 30]
    organics = [True, True, True, False, False, False]
    for (y, m), h, org in zip(base, healths, organics):
        when = datetime(y, m, 15)
        _health(db, fld, float(h), when)
        _treatment(db, fld, org, when)

    resp = client.get(f"/api/cooperatives/{coop.id}/monthly-progress?months=12")
    data = resp.json()
    assert data["overall_trend"] == "declining"


def test_monthly_progress_empty_months(client, db, coop):
    """Cooperative with farms but no data → empty months list, stable trend."""
    f = _farm(db, coop)
    _field(db, f)
    resp = client.get(f"/api/cooperatives/{coop.id}/monthly-progress")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cooperative_id"] == coop.id
    assert data["months"] == []
    assert data["overall_trend"] == "stable"


def test_monthly_progress_404(client):
    """Unknown cooperative → 404."""
    resp = client.get("/api/cooperatives/99999/monthly-progress")
    assert resp.status_code == 404
