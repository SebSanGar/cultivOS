"""Tests for GET /api/cooperatives/{coop_id}/action-plan."""

from datetime import datetime

from cultivos.db.models import (
    Cooperative,
    Farm,
    Field,
    ThermalResult,
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


def _thermal(db, field_id, stress_pct, at=None):
    t = ThermalResult(
        field_id=field_id,
        temp_mean=30.0,
        temp_std=2.0,
        temp_min=20.0,
        temp_max=40.0,
        pixels_total=1000,
        stress_pct=stress_pct,
        analyzed_at=at or datetime.utcnow(),
    )
    db.add(t)
    db.flush()
    return t


def test_404_unknown_cooperative(client):
    resp = client.get("/api/cooperatives/9999/action-plan")
    assert resp.status_code == 404


def test_empty_cooperative_returns_zero(client, db):
    c = _coop(db)
    db.commit()
    resp = client.get(f"/api/cooperatives/{c.id}/action-plan")
    assert resp.status_code == 200
    body = resp.json()
    assert body["cooperative_id"] == c.id
    assert body["period_days"] == 7
    assert body["total_fields_scanned"] == 0
    assert body["total_actions"] == 0
    assert body["high_count"] == 0
    assert body["medium_count"] == 0
    assert body["low_count"] == 0
    assert body["actions"] == []


def test_farm_without_cooperative_excluded(client, db):
    c = _coop(db)
    f_out = _farm(db, coop_id=None, name="Solo")
    fld = _field(db, f_out.id)
    _thermal(db, fld.id, stress_pct=85.0)
    db.commit()
    resp = client.get(f"/api/cooperatives/{c.id}/action-plan")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_fields_scanned"] == 0
    assert body["actions"] == []


def test_other_cooperative_excluded(client, db):
    c1 = _coop(db, name="Coop A")
    c2 = _coop(db, name="Coop B")
    f_in = _farm(db, coop_id=c1.id, name="In")
    f_out = _farm(db, coop_id=c2.id, name="Out")
    fld_in = _field(db, f_in.id, name="In Field")
    fld_out = _field(db, f_out.id, name="Out Field")
    _thermal(db, fld_in.id, stress_pct=85.0)
    _thermal(db, fld_out.id, stress_pct=85.0)
    db.commit()
    resp = client.get(f"/api/cooperatives/{c1.id}/action-plan")
    assert resp.status_code == 200
    body = resp.json()
    # Only 1 field scanned — Coop A has 1 field
    assert body["total_fields_scanned"] == 1
    # All returned actions must be from the In field
    for a in body["actions"]:
        assert a["field_id"] == fld_in.id
        assert a["farm_name"] == "In"


def test_high_priority_severe_thermal(client, db):
    c = _coop(db)
    f = _farm(db, coop_id=c.id)
    fld = _field(db, f.id)
    _thermal(db, fld.id, stress_pct=85.0)  # >= 70 → high thermal action
    db.commit()
    resp = client.get(f"/api/cooperatives/{c.id}/action-plan")
    body = resp.json()
    assert body["total_fields_scanned"] == 1
    assert body["high_count"] >= 1
    # At least one high-priority stress action present
    high_stress = [
        a for a in body["actions"]
        if a["priority"] == "high" and a["category"] == "stress"
    ]
    assert len(high_stress) >= 1
    # Enriched fields populated
    assert high_stress[0]["farm_id"] == f.id
    assert high_stress[0]["farm_name"] == f.name
    assert high_stress[0]["field_id"] == fld.id
    assert high_stress[0]["crop_type"] == "maiz"


def test_actions_sorted_high_before_low(client, db):
    c = _coop(db)
    f = _farm(db, coop_id=c.id)
    fld = _field(db, f.id)
    _thermal(db, fld.id, stress_pct=85.0)  # generates high + possibly low tek
    db.commit()
    resp = client.get(f"/api/cooperatives/{c.id}/action-plan")
    body = resp.json()
    priorities = [a["priority"] for a in body["actions"]]
    priority_rank = {"high": 0, "medium": 1, "low": 2}
    ranks = [priority_rank[p] for p in priorities]
    assert ranks == sorted(ranks), "Actions must be sorted high→medium→low"


def test_limit_parameter_caps_returned_actions(client, db):
    c = _coop(db)
    f = _farm(db, coop_id=c.id)
    # Make 3 fields each with severe thermal → 3+ actions total
    for i in range(3):
        fld = _field(db, f.id, name=f"F{i}")
        _thermal(db, fld.id, stress_pct=85.0)
    db.commit()
    resp = client.get(f"/api/cooperatives/{c.id}/action-plan?limit=2")
    body = resp.json()
    assert body["total_fields_scanned"] == 3
    # total_actions reflects all actions computed across all fields
    assert body["total_actions"] >= 3
    # returned actions capped at 2
    assert len(body["actions"]) == 2


def test_limit_out_of_bounds_returns_422(client, db):
    c = _coop(db)
    db.commit()
    resp = client.get(f"/api/cooperatives/{c.id}/action-plan?limit=500")
    assert resp.status_code == 422


def test_days_parameter_passed_through(client, db):
    c = _coop(db)
    f = _farm(db, coop_id=c.id)
    _field(db, f.id)
    db.commit()
    resp = client.get(f"/api/cooperatives/{c.id}/action-plan?days=14")
    body = resp.json()
    assert body["period_days"] == 14


def test_multi_farm_counts_and_enrichment(client, db):
    c = _coop(db)
    f1 = _farm(db, coop_id=c.id, name="Farm 1")
    f2 = _farm(db, coop_id=c.id, name="Farm 2")
    fld1 = _field(db, f1.id, name="F1", crop_type="maiz")
    fld2 = _field(db, f2.id, name="F2", crop_type="agave")
    _thermal(db, fld1.id, stress_pct=85.0)
    _thermal(db, fld2.id, stress_pct=85.0)
    db.commit()
    resp = client.get(f"/api/cooperatives/{c.id}/action-plan")
    body = resp.json()
    assert body["total_fields_scanned"] == 2
    farm_names = {a["farm_name"] for a in body["actions"]}
    assert farm_names == {"Farm 1", "Farm 2"}
    crop_types = {a["crop_type"] for a in body["actions"]}
    assert crop_types == {"maiz", "agave"}
