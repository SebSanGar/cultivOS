"""Tests for field crop calendar event log.

GET /api/farms/{farm_id}/fields/{field_id}/calendar?year=
Composes HealthScore + TreatmentRecord + FarmerObservation + AncestralMethod
into a 12-month timeline of event counts.
"""

from datetime import datetime

import pytest


@pytest.fixture
def farm(db):
    from cultivos.db.models import Farm
    f = Farm(name="Rancho Calendario", state="Jalisco", total_hectares=30.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@pytest.fixture
def other_farm(db):
    from cultivos.db.models import Farm
    f = Farm(name="Rancho Ajeno", state="Jalisco", total_hectares=10.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@pytest.fixture
def field(db, farm):
    from cultivos.db.models import Field
    fld = Field(farm_id=farm.id, name="Parcela Calendario", crop_type="maiz", hectares=4.0)
    db.add(fld)
    db.commit()
    db.refresh(fld)
    return fld


def _health(db, field, year, month, day=15, score=70.0):
    from cultivos.db.models import HealthScore
    hs = HealthScore(
        field_id=field.id,
        score=score,
        sources=["ndvi"],
        breakdown={"ndvi": score},
        scored_at=datetime(year, month, day),
    )
    db.add(hs)
    db.commit()


def _treatment(db, field, year, month, day=10):
    from cultivos.db.models import TreatmentRecord
    t = TreatmentRecord(
        field_id=field.id,
        health_score_used=60.0,
        problema="plaga",
        causa_probable="hongo",
        tratamiento="compost",
        costo_estimado_mxn=100,
        urgencia="media",
        prevencion="rotacion",
        organic=True,
        applied_at=datetime(year, month, day),
    )
    db.add(t)
    db.commit()


def _observation(db, field, year, month, day=5, obs_type="neutral"):
    from cultivos.db.models import FarmerObservation
    o = FarmerObservation(
        field_id=field.id,
        observation_es="El cultivo se ve bien",
        observation_type=obs_type,
        created_at=datetime(year, month, day),
    )
    db.add(o)
    db.commit()


def _tek_practice(db, name, crops, months, ecological_benefit=3):
    from cultivos.db.models import AncestralMethod
    m = AncestralMethod(
        name=name,
        description_es="Practica tradicional",
        region="Jalisco",
        practice_type="soil_management",
        crops=crops,
        benefits_es="Beneficia el suelo",
        applicable_months=months,
        timing_rationale="Por temporada",
        ecological_benefit=ecological_benefit,
    )
    db.add(m)
    db.commit()
    return m


def test_calendar_unknown_farm(client):
    resp = client.get("/api/farms/9999/fields/1/calendar")
    assert resp.status_code == 404


def test_calendar_unknown_field(client, farm):
    resp = client.get(f"/api/farms/{farm.id}/fields/9999/calendar")
    assert resp.status_code == 404


def test_calendar_field_from_other_farm(client, db, farm, other_farm):
    from cultivos.db.models import Field
    foreign = Field(farm_id=other_farm.id, name="Ajena", crop_type="frijol", hectares=2.0)
    db.add(foreign)
    db.commit()
    db.refresh(foreign)
    resp = client.get(f"/api/farms/{farm.id}/fields/{foreign.id}/calendar")
    assert resp.status_code == 404


def test_calendar_empty_field_returns_12_zero_months(client, farm, field):
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/calendar?year=2026")
    assert resp.status_code == 200
    data = resp.json()
    assert data["farm_id"] == farm.id
    assert data["field_id"] == field.id
    assert data["year"] == 2026
    assert data["crop_type"] == "maiz"
    assert len(data["months"]) == 12
    assert [m["month"] for m in data["months"]] == list(range(1, 13))
    for m in data["months"]:
        assert m["health_scores"] == 0
        assert m["treatments"] == 0
        assert m["observations"] == 0
        assert m["tek_practices"] == 0
        assert m["total_events"] == 0
    assert data["total_events"] == 0
    assert data["busiest_month"] is None


def test_calendar_year_filter_excludes_other_years(client, db, farm, field):
    _health(db, field, year=2025, month=6)
    _health(db, field, year=2026, month=6)
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/calendar?year=2026")
    data = resp.json()
    assert data["year"] == 2026
    assert data["months"][5]["health_scores"] == 1
    assert data["total_events"] == 1


def test_calendar_counts_health_scores_per_month(client, db, farm, field):
    _health(db, field, 2026, 6)
    _health(db, field, 2026, 6, day=20)
    _health(db, field, 2026, 8)
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/calendar?year=2026")
    data = resp.json()
    assert data["months"][5]["health_scores"] == 2  # June
    assert data["months"][7]["health_scores"] == 1  # August
    assert data["total_events"] == 3


def test_calendar_counts_treatments_per_month(client, db, farm, field):
    _treatment(db, field, 2026, 7)
    _treatment(db, field, 2026, 7, day=20)
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/calendar?year=2026")
    data = resp.json()
    assert data["months"][6]["treatments"] == 2
    assert data["total_events"] == 2


def test_calendar_counts_observations_per_month(client, db, farm, field):
    _observation(db, field, 2026, 8)
    _observation(db, field, 2026, 3, obs_type="problem")
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/calendar?year=2026")
    data = resp.json()
    assert data["months"][7]["observations"] == 1
    assert data["months"][2]["observations"] == 1
    assert data["total_events"] == 2


def test_calendar_counts_tek_practices_by_crop_and_month(client, db, farm, field):
    _tek_practice(db, "Milpa rotation", crops=["maiz", "frijol"], months=[6, 7, 8])
    _tek_practice(db, "Dry pruning", crops=["agave"], months=[11, 12])
    _tek_practice(db, "Terraced soil", crops=["maiz"], months=[1, 2, 3])
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/calendar?year=2026")
    data = resp.json()
    # maiz field: milpa + terraced apply; agave practice excluded
    assert data["months"][0]["tek_practices"] == 1  # Jan — Terraced
    assert data["months"][1]["tek_practices"] == 1  # Feb — Terraced
    assert data["months"][2]["tek_practices"] == 1  # Mar — Terraced
    assert data["months"][5]["tek_practices"] == 1  # Jun — Milpa
    assert data["months"][6]["tek_practices"] == 1  # Jul — Milpa
    assert data["months"][7]["tek_practices"] == 1  # Aug — Milpa
    assert data["months"][10]["tek_practices"] == 0  # Nov — excluded
    assert data["months"][11]["tek_practices"] == 0  # Dec — excluded


def test_calendar_busiest_month_and_total(client, db, farm, field):
    _health(db, field, 2026, 6)
    _health(db, field, 2026, 6)
    _treatment(db, field, 2026, 6)
    _observation(db, field, 2026, 3)
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/calendar?year=2026")
    data = resp.json()
    assert data["months"][5]["total_events"] == 3
    assert data["months"][2]["total_events"] == 1
    assert data["total_events"] == 4
    assert data["busiest_month"] == 6


def test_calendar_year_defaults_to_current(client, db, farm, field):
    current_year = datetime.utcnow().year
    _health(db, field, current_year, 6)
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/calendar")
    assert resp.status_code == 200
    data = resp.json()
    assert data["year"] == current_year
    assert data["months"][5]["health_scores"] == 1
