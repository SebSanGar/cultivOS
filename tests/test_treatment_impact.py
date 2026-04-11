"""Tests for GET /api/farms/{farm_id}/treatment-impact endpoint.

Returns per-(crop_type, problema) treatment effectiveness for the farm's fields,
computed using 30-day HealthScore followup after each treatment.
"""

import pytest
from datetime import datetime, timedelta
from cultivos.db.models import Farm, Field, TreatmentRecord, HealthScore


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_farm(db, name="Rancho Impact"):
    farm = Farm(name=name, state="Jalisco", total_hectares=10.0)
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id, name="Campo A", crop_type="maiz"):
    field = Field(farm_id=farm_id, name=name, crop_type=crop_type, hectares=5.0)
    db.add(field)
    db.commit()
    return field


def _add_treatment(db, field_id, problema="plagas", days_ago=30, health=60.0):
    t = TreatmentRecord(
        field_id=field_id,
        health_score_used=health,
        problema=problema,
        causa_probable="Insectos chupadores detectados por NDVI",
        tratamiento="Aplicar jabón potásico al 1%",
        costo_estimado_mxn=200,
        urgencia="media",
        prevencion="Monitoreo semanal en temporada de lluvias",
        organic=True,
        created_at=datetime.utcnow() - timedelta(days=days_ago),
    )
    db.add(t)
    db.commit()
    return t


def _add_health_score(db, field_id, score, days_ago=0):
    hs = HealthScore(
        field_id=field_id,
        score=score,
        scored_at=datetime.utcnow() - timedelta(days=days_ago),
    )
    db.add(hs)
    db.commit()
    return hs


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_404_unknown_farm(client, db):
    r = client.get("/api/farms/9999/treatment-impact")
    assert r.status_code == 404


def test_response_schema_keys(client, db):
    """Response contains farm_id, period_days, and treatments list."""
    farm = _make_farm(db)
    r = client.get(f"/api/farms/{farm.id}/treatment-impact")
    assert r.status_code == 200
    data = r.json()
    for key in ("farm_id", "period_days", "treatments"):
        assert key in data, f"Missing key: {key}"
    assert data["farm_id"] == farm.id
    assert data["period_days"] == 90  # default


def test_no_treatments_returns_empty(client, db):
    """Farm with no treatment records returns empty treatments list."""
    farm = _make_farm(db)
    _make_field(db, farm.id)
    r = client.get(f"/api/farms/{farm.id}/treatment-impact")
    assert r.status_code == 200
    assert r.json()["treatments"] == []


def test_treatment_without_followup_excluded(client, db):
    """Treatment with no HealthScore followup within 30 days is not counted."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_treatment(db, field.id, days_ago=5)
    # No followup health score added → should not appear in results

    r = client.get(f"/api/farms/{farm.id}/treatment-impact")
    assert r.status_code == 200
    assert r.json()["treatments"] == []


def test_correct_health_delta_computed(client, db):
    """Treatment at health=60, followup score=75 → delta = +15."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    # Treatment 20 days ago at health=60
    _add_treatment(db, field.id, problema="plagas", days_ago=20, health=60.0)
    # Followup health score 10 days ago (within 30-day window)
    _add_health_score(db, field.id, score=75.0, days_ago=10)

    r = client.get(f"/api/farms/{farm.id}/treatment-impact")
    assert r.status_code == 200
    data = r.json()
    assert len(data["treatments"]) == 1
    item = data["treatments"][0]
    assert item["avg_health_delta"] == pytest.approx(15.0, abs=0.1)
    assert item["crop_type"] == "maiz"
    assert item["problema"] == "plagas"
    assert item["count"] == 1


def test_multiple_treatments_same_group_averaged(client, db):
    """Two plagas treatments → avg of their deltas."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    # First treatment 25 days ago, delta = +10
    _add_treatment(db, field.id, problema="plagas", days_ago=25, health=60.0)
    _add_health_score(db, field.id, score=70.0, days_ago=15)
    # Second treatment 50 days ago, delta = +20
    _add_treatment(db, field.id, problema="plagas", days_ago=50, health=50.0)
    _add_health_score(db, field.id, score=70.0, days_ago=40)

    r = client.get(f"/api/farms/{farm.id}/treatment-impact")
    assert r.status_code == 200
    data = r.json()
    treatments = data["treatments"]
    assert len(treatments) >= 1
    # Both belong to same group — avg should be ~15 (10+20)/2
    plagas = next((t for t in treatments if t["problema"] == "plagas"), None)
    assert plagas is not None
    assert plagas["count"] == 2
    assert plagas["avg_health_delta"] == pytest.approx(15.0, abs=1.0)


def test_different_grupos_separate_rows(client, db):
    """plagas and sequia treatments appear as separate rows."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_treatment(db, field.id, problema="plagas", days_ago=20, health=60.0)
    _add_health_score(db, field.id, score=75.0, days_ago=10)
    _add_treatment(db, field.id, problema="sequia", days_ago=45, health=40.0)
    _add_health_score(db, field.id, score=55.0, days_ago=35)

    r = client.get(f"/api/farms/{farm.id}/treatment-impact")
    assert r.status_code == 200
    tratamientos = r.json()["treatments"]
    problemas = {t["problema"] for t in tratamientos}
    assert "plagas" in problemas
    assert "sequia" in problemas


def test_days_filter_excludes_old_treatments(client, db):
    """Treatment 200 days ago is outside the 90-day window."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_treatment(db, field.id, problema="plagas", days_ago=200, health=60.0)
    _add_health_score(db, field.id, score=80.0, days_ago=180)

    r = client.get(f"/api/farms/{farm.id}/treatment-impact?days=90")
    assert r.status_code == 200
    assert r.json()["treatments"] == []


def test_custom_days_parameter(client, db):
    """days=30 parameter is respected."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_treatment(db, field.id, problema="hongos", days_ago=20, health=55.0)
    _add_health_score(db, field.id, score=70.0, days_ago=10)

    r = client.get(f"/api/farms/{farm.id}/treatment-impact?days=30")
    assert r.status_code == 200
    data = r.json()
    assert data["period_days"] == 30
    assert len(data["treatments"]) == 1


def test_excludes_other_farms_treatments(client, db):
    """Treatments from other farm fields are not included."""
    farm1 = _make_farm(db, name="Farm A")
    farm2 = _make_farm(db, name="Farm B")
    field1 = _make_field(db, farm1.id)
    field2 = _make_field(db, farm2.id)
    # Treatment on farm2's field only
    _add_treatment(db, field2.id, problema="plagas", days_ago=20, health=60.0)
    _add_health_score(db, field2.id, score=80.0, days_ago=10)

    r = client.get(f"/api/farms/{farm1.id}/treatment-impact")
    assert r.status_code == 200
    assert r.json()["treatments"] == []


def test_interpretation_es_present(client, db):
    """Each treatment item has a non-empty Spanish interpretation."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_treatment(db, field.id, problema="plagas", days_ago=20, health=60.0)
    _add_health_score(db, field.id, score=78.0, days_ago=10)

    r = client.get(f"/api/farms/{farm.id}/treatment-impact")
    assert r.status_code == 200
    item = r.json()["treatments"][0]
    assert "interpretation_es" in item
    assert isinstance(item["interpretation_es"], str)
    assert len(item["interpretation_es"]) > 5


def test_item_schema_keys(client, db):
    """Each treatment item has all required keys."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_treatment(db, field.id, problema="plagas", days_ago=20, health=60.0)
    _add_health_score(db, field.id, score=80.0, days_ago=10)

    r = client.get(f"/api/farms/{farm.id}/treatment-impact")
    assert r.status_code == 200
    item = r.json()["treatments"][0]
    for key in ("crop_type", "problema", "count", "avg_health_delta", "interpretation_es"):
        assert key in item, f"Missing key: {key}"
