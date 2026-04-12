"""Tests for GET /api/cooperatives/{coop_id}/tek-adoption?month=

Task #192: Cooperative TEK practice adoption rate.
Composes compute_tek_alignment per field across all member farms.
"""

from datetime import datetime

import pytest

from cultivos.db.models import (
    AncestralMethod,
    Cooperative,
    Farm,
    Field,
    SoilAnalysis,
)


# ── Helpers ────────────────────────────────────────────────────────────────────


def _coop(db, name="Coop Adopcion"):
    c = Cooperative(name=name, state="Jalisco")
    db.add(c)
    db.flush()
    return c


def _farm(db, coop_id=None, name="Farm A"):
    f = Farm(name=name, state="Jalisco", total_hectares=10.0, cooperative_id=coop_id)
    db.add(f)
    db.flush()
    return f


def _field(db, farm_id, crop_type="maiz", name="Lote 1"):
    fld = Field(farm_id=farm_id, name=name, hectares=5.0, crop_type=crop_type)
    db.add(fld)
    db.flush()
    return fld


def _tek(db, name, practice_type, months, crops=None, benefit=4):
    m = AncestralMethod(
        name=name,
        description_es=f"Descripcion {name}",
        region="jalisco",
        practice_type=practice_type,
        crops=crops or ["maiz"],
        benefits_es="Mejora el suelo",
        problems=["drought"],
        applicable_months=months,
        timing_rationale="Momento ideal del ciclo",
        ecological_benefit=benefit,
    )
    db.add(m)
    db.flush()
    return m


def _dry_soil(db, field_id):
    """moisture_pct=15 triggers water stress → water_management practices supported."""
    db.add(SoilAnalysis(
        field_id=field_id,
        ph=6.5, organic_matter_pct=2.0,
        nitrogen_ppm=20, phosphorus_ppm=15, potassium_ppm=180,
        moisture_pct=15.0,
        sampled_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    ))
    db.flush()


# ── Tests ──────────────────────────────────────────────────────────────────────


def test_404_unknown_cooperative(client):
    resp = client.get("/api/cooperatives/9999/tek-adoption?month=6")
    assert resp.status_code == 404


def test_empty_cooperative(client, db):
    c = _coop(db)
    db.commit()
    resp = client.get(f"/api/cooperatives/{c.id}/tek-adoption?month=6")
    assert resp.status_code == 200
    body = resp.json()
    assert body["cooperative_id"] == c.id
    assert body["month"] == 6
    assert body["farms"] == []
    assert body["overall_adoption_pct"] == 0.0
    assert body["top_practice_es"] is None
    assert body["total_fields_assessed"] == 0


def test_single_farm_single_supported_field(client, db):
    c = _coop(db)
    f = _farm(db, coop_id=c.id, name="Finca Uno")
    fld = _field(db, f.id, crop_type="maiz")
    _dry_soil(db, fld.id)  # → water_active
    _tek(db, "Acequia tradicional", "water_management", [6], crops=["maiz"])
    db.commit()

    resp = client.get(f"/api/cooperatives/{c.id}/tek-adoption?month=6")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_fields_assessed"] == 1
    assert body["overall_adoption_pct"] == 100.0
    assert body["top_practice_es"] == "Acequia tradicional"
    assert len(body["farms"]) == 1
    fm = body["farms"][0]
    assert fm["farm_id"] == f.id
    assert fm["farm_name"] == "Finca Uno"
    assert fm["avg_alignment_pct"] == 100.0
    assert fm["fields_assessed"] == 1


def test_multi_farm_averaging(client, db):
    c = _coop(db)
    f1 = _farm(db, coop_id=c.id, name="Farm 1")
    f2 = _farm(db, coop_id=c.id, name="Farm 2")
    fld1 = _field(db, f1.id, crop_type="maiz", name="F1 Lote")
    fld2 = _field(db, f2.id, crop_type="maiz", name="F2 Lote")
    _dry_soil(db, fld1.id)  # fld1 supports water_management
    # fld2: no dry soil → water_management NOT supported
    _tek(db, "Acequia", "water_management", [6], crops=["maiz"])
    db.commit()

    resp = client.get(f"/api/cooperatives/{c.id}/tek-adoption?month=6")
    body = resp.json()
    assert body["total_fields_assessed"] == 2
    # fld1 = 100%, fld2 = 0% → mean 50%
    assert body["overall_adoption_pct"] == 50.0
    assert len(body["farms"]) == 2
    by_name = {fm["farm_name"]: fm for fm in body["farms"]}
    assert by_name["Farm 1"]["avg_alignment_pct"] == 100.0
    assert by_name["Farm 2"]["avg_alignment_pct"] == 0.0


def test_month_defaults_to_current(client, db, monkeypatch):
    """When month query param omitted, service uses current calendar month."""
    from cultivos.services.intelligence import coop_tek_adoption as svc

    class FakeDate:
        @classmethod
        def today(cls):
            import datetime as _dt
            return _dt.date(2026, 6, 15)

    monkeypatch.setattr(svc, "date", FakeDate)

    c = _coop(db)
    f = _farm(db, coop_id=c.id)
    fld = _field(db, f.id, crop_type="maiz")
    _dry_soil(db, fld.id)
    _tek(db, "Acequia", "water_management", [6], crops=["maiz"])
    db.commit()

    resp = client.get(f"/api/cooperatives/{c.id}/tek-adoption")
    assert resp.status_code == 200
    body = resp.json()
    assert body["month"] == 6
    assert body["overall_adoption_pct"] == 100.0


def test_field_without_applicable_practices_excluded(client, db):
    c = _coop(db)
    f = _farm(db, coop_id=c.id)
    fld = _field(db, f.id, crop_type="agave")  # TEK targets maiz, not agave
    _dry_soil(db, fld.id)
    _tek(db, "Acequia", "water_management", [6], crops=["maiz"])
    db.commit()

    resp = client.get(f"/api/cooperatives/{c.id}/tek-adoption?month=6")
    body = resp.json()
    assert body["total_fields_assessed"] == 0
    assert body["overall_adoption_pct"] == 0.0
    assert body["top_practice_es"] is None
    assert body["farms"][0]["fields_assessed"] == 0
    assert body["farms"][0]["avg_alignment_pct"] == 0.0


def test_top_practice_by_support_count(client, db):
    c = _coop(db)
    f = _farm(db, coop_id=c.id)
    fld1 = _field(db, f.id, crop_type="maiz", name="L1")
    fld2 = _field(db, f.id, crop_type="maiz", name="L2")
    _dry_soil(db, fld1.id)
    _dry_soil(db, fld2.id)
    # Practice A supports both fields (water_management, water stress present)
    _tek(db, "Acequia madre", "water_management", [6], crops=["maiz"])
    # Practice B does NOT support (soil_management requires disease_elevated)
    _tek(db, "Composta", "soil_management", [6], crops=["maiz"])
    db.commit()

    resp = client.get(f"/api/cooperatives/{c.id}/tek-adoption?month=6")
    body = resp.json()
    assert body["top_practice_es"] == "Acequia madre"


def test_month_below_range_rejected(client, db):
    c = _coop(db)
    db.commit()
    resp = client.get(f"/api/cooperatives/{c.id}/tek-adoption?month=0")
    assert resp.status_code == 422


def test_month_above_range_rejected(client, db):
    c = _coop(db)
    db.commit()
    resp = client.get(f"/api/cooperatives/{c.id}/tek-adoption?month=13")
    assert resp.status_code == 422
