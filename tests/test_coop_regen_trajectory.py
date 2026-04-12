"""Tests for GET /api/cooperatives/{coop_id}/regen-trajectory

Task #194: Cooperative regen trajectory aggregate.
Composes compute_regen_trajectory per member farm, merges monthly regen scores
across farms into a cooperative-wide longitudinal series.
"""

from datetime import datetime, timedelta

from cultivos.db.models import (
    Cooperative,
    Farm,
    Field,
    HealthScore,
    TreatmentRecord,
)


# ── Helpers ────────────────────────────────────────────────────────────────────


def _coop(db, name="Coop Regen"):
    c = Cooperative(name=name, state="Jalisco")
    db.add(c)
    db.flush()
    return c


def _farm(db, coop_id=None, name="Farm"):
    f = Farm(name=name, state="Jalisco", total_hectares=10.0, cooperative_id=coop_id)
    db.add(f)
    db.flush()
    return f


def _field(db, farm_id, name="Lote"):
    fld = Field(farm_id=farm_id, name=name, hectares=5.0, crop_type="maiz")
    db.add(fld)
    db.flush()
    return fld


def _health(db, field_id, score, months_ago):
    when = datetime.utcnow() - timedelta(days=30 * months_ago)
    db.add(HealthScore(field_id=field_id, score=score, scored_at=when))
    db.flush()


def _treatment(db, field_id, organic, months_ago):
    when = datetime.utcnow() - timedelta(days=30 * months_ago)
    db.add(TreatmentRecord(
        field_id=field_id,
        health_score_used=60.0,
        problema="plagas",
        causa_probable="desconocida",
        tratamiento="compost",
        costo_estimado_mxn=0,
        urgencia="media",
        prevencion="rotacion",
        organic=organic,
        created_at=when,
    ))
    db.flush()


# ── Tests ──────────────────────────────────────────────────────────────────────


def test_404_unknown_cooperative(client):
    resp = client.get("/api/cooperatives/9999/regen-trajectory")
    assert resp.status_code == 404


def test_empty_cooperative(client, db):
    c = _coop(db)
    db.commit()
    resp = client.get(f"/api/cooperatives/{c.id}/regen-trajectory")
    assert resp.status_code == 200
    body = resp.json()
    assert body["cooperative_id"] == c.id
    assert body["overall_months"] == []
    assert body["overall_trend"] == "stable"
    assert body["farms"] == []
    assert body["farms_count"] == 0


def test_single_farm_single_month(client, db):
    c = _coop(db)
    f = _farm(db, coop_id=c.id, name="Finca Uno")
    fld = _field(db, f.id)
    _health(db, fld.id, 80.0, months_ago=1)
    _treatment(db, fld.id, organic=True, months_ago=1)
    db.commit()

    resp = client.get(f"/api/cooperatives/{c.id}/regen-trajectory")
    body = resp.json()
    assert body["farms_count"] == 1
    assert len(body["overall_months"]) == 1
    m = body["overall_months"][0]
    # organic_pct=100 → 100*0.6 + 80*0.4 = 92.0
    assert m["avg_regen_score"] == 92.0
    assert m["farms_contributing"] == 1
    assert len(body["farms"]) == 1
    farm_entry = body["farms"][0]
    assert farm_entry["farm_id"] == f.id
    assert farm_entry["farm_name"] == "Finca Uno"
    assert farm_entry["months_count"] == 1
    assert farm_entry["latest_regen_score"] == 92.0
    assert farm_entry["trend"] == "stable"


def test_multi_farm_same_month_averaged(client, db):
    """Two farms with data in same month → overall avg is mean of per-farm scores."""
    c = _coop(db)
    f1 = _farm(db, coop_id=c.id, name="F1")
    f2 = _farm(db, coop_id=c.id, name="F2")
    fld1 = _field(db, f1.id)
    fld2 = _field(db, f2.id)
    # Farm 1: 100% organic, avg health 80 → 92.0
    _health(db, fld1.id, 80.0, months_ago=1)
    _treatment(db, fld1.id, organic=True, months_ago=1)
    # Farm 2: 0% organic, avg health 60 → 0*0.6 + 60*0.4 = 24.0
    _health(db, fld2.id, 60.0, months_ago=1)
    _treatment(db, fld2.id, organic=False, months_ago=1)
    db.commit()

    resp = client.get(f"/api/cooperatives/{c.id}/regen-trajectory")
    body = resp.json()
    assert body["farms_count"] == 2
    assert len(body["overall_months"]) == 1
    m = body["overall_months"][0]
    # (92.0 + 24.0) / 2 = 58.0
    assert m["avg_regen_score"] == 58.0
    assert m["farms_contributing"] == 2


def test_multi_month_disjoint_coverage(client, db):
    """Farm A has month X, Farm B has month Y → both appear with farms_contributing=1."""
    c = _coop(db)
    f1 = _farm(db, coop_id=c.id, name="A")
    f2 = _farm(db, coop_id=c.id, name="B")
    fld1 = _field(db, f1.id)
    fld2 = _field(db, f2.id)
    _health(db, fld1.id, 80.0, months_ago=2)
    _treatment(db, fld1.id, organic=True, months_ago=2)
    _health(db, fld2.id, 50.0, months_ago=1)
    _treatment(db, fld2.id, organic=True, months_ago=1)
    db.commit()

    resp = client.get(f"/api/cooperatives/{c.id}/regen-trajectory")
    body = resp.json()
    months = body["overall_months"]
    assert len(months) == 2
    # Sorted ASC
    assert months[0]["month"] < months[1]["month"]
    for m in months:
        assert m["farms_contributing"] == 1


def test_overall_trend_improving(client, db):
    """8 months of data, last 3 avg > first 3 avg by > 5 points."""
    c = _coop(db)
    f = _farm(db, coop_id=c.id)
    fld = _field(db, f.id)
    # Months 8..1 ago, health ramping up 40 → 90 (all organic)
    healths = [40, 45, 50, 60, 70, 80, 85, 90]
    for idx, h in enumerate(healths):
        months_ago = 8 - idx
        _health(db, fld.id, float(h), months_ago=months_ago)
        _treatment(db, fld.id, organic=True, months_ago=months_ago)
    db.commit()

    resp = client.get(f"/api/cooperatives/{c.id}/regen-trajectory")
    body = resp.json()
    assert body["overall_trend"] == "improving"
    assert body["farms"][0]["trend"] == "improving"


def test_overall_trend_declining(client, db):
    c = _coop(db)
    f = _farm(db, coop_id=c.id)
    fld = _field(db, f.id)
    healths = [90, 85, 80, 70, 60, 50, 45, 40]
    for idx, h in enumerate(healths):
        months_ago = 8 - idx
        _health(db, fld.id, float(h), months_ago=months_ago)
        _treatment(db, fld.id, organic=True, months_ago=months_ago)
    db.commit()

    resp = client.get(f"/api/cooperatives/{c.id}/regen-trajectory")
    body = resp.json()
    assert body["overall_trend"] == "declining"


def test_overall_trend_stable_insufficient_data(client, db):
    """< 6 months of overall data → trend stable even if values differ."""
    c = _coop(db)
    f = _farm(db, coop_id=c.id)
    fld = _field(db, f.id)
    for months_ago in (4, 3, 2, 1):
        _health(db, fld.id, 80.0, months_ago=months_ago)
        _treatment(db, fld.id, organic=True, months_ago=months_ago)
    db.commit()

    resp = client.get(f"/api/cooperatives/{c.id}/regen-trajectory")
    body = resp.json()
    assert body["overall_trend"] == "stable"


def test_unaffiliated_farm_excluded(client, db):
    """Farm without cooperative_id must not leak into coop aggregate."""
    c = _coop(db)
    member = _farm(db, coop_id=c.id, name="Member")
    outsider = _farm(db, coop_id=None, name="Outsider")
    mfield = _field(db, member.id)
    ofield = _field(db, outsider.id)
    _health(db, mfield.id, 80.0, months_ago=1)
    _treatment(db, mfield.id, organic=True, months_ago=1)
    _health(db, ofield.id, 10.0, months_ago=1)
    _treatment(db, ofield.id, organic=False, months_ago=1)
    db.commit()

    resp = client.get(f"/api/cooperatives/{c.id}/regen-trajectory")
    body = resp.json()
    assert body["farms_count"] == 1
    assert body["farms"][0]["farm_name"] == "Member"
    # Should reflect only the member's 92.0, not dragged down by outsider
    assert body["overall_months"][0]["avg_regen_score"] == 92.0
