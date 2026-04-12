"""Tests for GET /api/cooperatives/{coop_id}/treatment-effectiveness."""

from datetime import datetime, timedelta

import pytest

from cultivos.db.models import (
    Cooperative,
    Farm,
    Field,
    HealthScore,
    TreatmentRecord,
)


def _coop(db, name="Coop A"):
    c = Cooperative(name=name, state="Jalisco")
    db.add(c)
    db.flush()
    return c


def _farm(db, coop_id=None, name="Farm X"):
    f = Farm(name=name, state="Jalisco", total_hectares=20.0, cooperative_id=coop_id)
    db.add(f)
    db.flush()
    return f


def _field(db, farm_id, crop_type="maiz", name="Field 1"):
    fld = Field(farm_id=farm_id, name=name, hectares=5.0, crop_type=crop_type)
    db.add(fld)
    db.flush()
    return fld


def _treat(db, field_id, problema, score_used=50.0, at=None):
    if at is None:
        at = datetime(2026, 1, 10)
    t = TreatmentRecord(
        field_id=field_id,
        problema=problema,
        causa_probable="test",
        tratamiento="apply organic compost",
        costo_estimado_mxn=500,
        urgencia="media",
        prevencion="rotate crops",
        organic=True,
        health_score_used=score_used,
        created_at=at,
    )
    db.add(t)
    db.flush()
    return t


def _hs(db, field_id, score, at):
    h = HealthScore(
        field_id=field_id,
        score=score,
        sources=["test"],
        breakdown={},
        scored_at=at,
        created_at=at,
    )
    db.add(h)
    db.flush()
    return h


def test_404_unknown_cooperative(client):
    resp = client.get("/api/cooperatives/9999/treatment-effectiveness")
    assert resp.status_code == 404


def test_empty_cooperative_returns_empty_groups(client, db):
    c = _coop(db)
    db.commit()
    resp = client.get(f"/api/cooperatives/{c.id}/treatment-effectiveness")
    assert resp.status_code == 200
    body = resp.json()
    assert body["cooperative_id"] == c.id
    assert body["groups"] == []


def test_single_farm_single_treatment(client, db):
    c = _coop(db)
    f = _farm(db, coop_id=c.id)
    fld = _field(db, f.id, crop_type="maiz")
    t_date = datetime(2026, 1, 10)
    _treat(db, fld.id, "plagas", score_used=50.0, at=t_date)
    _hs(db, fld.id, 70.0, t_date + timedelta(days=10))
    db.commit()

    resp = client.get(f"/api/cooperatives/{c.id}/treatment-effectiveness")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["groups"]) == 1
    g = body["groups"][0]
    assert g["crop_type"] == "maiz"
    assert g["treatment_summary"] == "plagas"
    assert g["avg_health_delta"] == pytest.approx(20.0)
    assert g["usage_count"] == 1
    assert g["participating_farms_count"] == 1


def test_multi_farm_aggregation_counts_distinct_farms(client, db):
    c = _coop(db)
    f1 = _farm(db, coop_id=c.id, name="Farm 1")
    f2 = _farm(db, coop_id=c.id, name="Farm 2")
    fld1 = _field(db, f1.id, crop_type="maiz")
    fld2 = _field(db, f2.id, crop_type="maiz")
    t_date = datetime(2026, 2, 1)
    _treat(db, fld1.id, "plagas", score_used=40.0, at=t_date)
    _treat(db, fld2.id, "plagas", score_used=60.0, at=t_date)
    _hs(db, fld1.id, 60.0, t_date + timedelta(days=5))  # delta +20
    _hs(db, fld2.id, 70.0, t_date + timedelta(days=5))  # delta +10
    db.commit()

    resp = client.get(f"/api/cooperatives/{c.id}/treatment-effectiveness")
    assert resp.status_code == 200
    groups = resp.json()["groups"]
    assert len(groups) == 1
    g = groups[0]
    assert g["avg_health_delta"] == pytest.approx(15.0)
    assert g["usage_count"] == 2
    assert g["participating_farms_count"] == 2


def test_other_cooperative_excluded(client, db):
    c1 = _coop(db, name="Coop A")
    c2 = _coop(db, name="Coop B")
    f_in = _farm(db, coop_id=c1.id, name="In")
    f_out = _farm(db, coop_id=c2.id, name="Out")
    fld_in = _field(db, f_in.id, crop_type="maiz")
    fld_out = _field(db, f_out.id, crop_type="maiz")
    t_date = datetime(2026, 3, 1)
    _treat(db, fld_in.id, "plagas", score_used=50.0, at=t_date)
    _treat(db, fld_out.id, "plagas", score_used=50.0, at=t_date)
    _hs(db, fld_in.id, 70.0, t_date + timedelta(days=5))
    _hs(db, fld_out.id, 90.0, t_date + timedelta(days=5))  # should not contaminate
    db.commit()

    resp = client.get(f"/api/cooperatives/{c1.id}/treatment-effectiveness")
    groups = resp.json()["groups"]
    assert len(groups) == 1
    assert groups[0]["avg_health_delta"] == pytest.approx(20.0)
    assert groups[0]["participating_farms_count"] == 1


def test_groups_sorted_desc_by_avg_delta(client, db):
    c = _coop(db)
    f = _farm(db, coop_id=c.id)
    fld_maiz = _field(db, f.id, crop_type="maiz", name="Maiz field")
    fld_agave = _field(db, f.id, crop_type="agave", name="Agave field")
    t_date = datetime(2026, 2, 15)
    _treat(db, fld_maiz.id, "plagas", score_used=50.0, at=t_date)
    _hs(db, fld_maiz.id, 55.0, t_date + timedelta(days=5))  # delta +5
    _treat(db, fld_agave.id, "sequia", score_used=40.0, at=t_date)
    _hs(db, fld_agave.id, 70.0, t_date + timedelta(days=5))  # delta +30
    db.commit()

    resp = client.get(f"/api/cooperatives/{c.id}/treatment-effectiveness")
    groups = resp.json()["groups"]
    assert len(groups) == 2
    assert groups[0]["crop_type"] == "agave"
    assert groups[0]["avg_health_delta"] == pytest.approx(30.0)
    assert groups[1]["crop_type"] == "maiz"
    assert groups[1]["avg_health_delta"] == pytest.approx(5.0)


def test_treatment_without_followup_excluded(client, db):
    c = _coop(db)
    f = _farm(db, coop_id=c.id)
    fld = _field(db, f.id, crop_type="maiz")
    t_date = datetime(2026, 1, 10)
    _treat(db, fld.id, "plagas", score_used=50.0, at=t_date)
    # No health score follow-up
    db.commit()

    resp = client.get(f"/api/cooperatives/{c.id}/treatment-effectiveness")
    assert resp.status_code == 200
    assert resp.json()["groups"] == []


def test_farm_without_cooperative_excluded(client, db):
    c = _coop(db)
    f_unaffiliated = _farm(db, coop_id=None, name="Solo")
    fld = _field(db, f_unaffiliated.id, crop_type="maiz")
    t_date = datetime(2026, 1, 10)
    _treat(db, fld.id, "plagas", score_used=50.0, at=t_date)
    _hs(db, fld.id, 80.0, t_date + timedelta(days=5))
    db.commit()

    resp = client.get(f"/api/cooperatives/{c.id}/treatment-effectiveness")
    assert resp.json()["groups"] == []
