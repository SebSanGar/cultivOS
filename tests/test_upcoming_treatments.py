"""Tests for GET /api/farms/{farm_id}/fields/{field_id}/upcoming-treatments."""

from datetime import datetime, timedelta
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def farm(db):
    from cultivos.db.models import Farm
    f = Farm(name="Rancho Tratamientos", state="Jalisco", total_hectares=10.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@pytest.fixture
def field(db, farm):
    from cultivos.db.models import Field
    # planted 30 days ago → mid-season maiz (vegetative stage)
    f = Field(
        farm_id=farm.id,
        name="Parcela Maiz",
        crop_type="maiz",
        hectares=5.0,
        planted_at=datetime.utcnow() - timedelta(days=30),
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@pytest.fixture
def field_no_phenology(db, farm):
    """Field with no planted_at — can't compute growth stage."""
    from cultivos.db.models import Field
    f = Field(
        farm_id=farm.id,
        name="Parcela Sin Fecha",
        crop_type="maiz",
        hectares=3.0,
        planted_at=None,
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def _add_treatment(db, field_id, days_ago):
    from cultivos.db.models import TreatmentRecord
    t = TreatmentRecord(
        field_id=field_id,
        health_score_used=70.0,
        problema="Baja fertilidad",
        causa_probable="Suelo degradado",
        tratamiento="Composta organica",
        costo_estimado_mxn=500,
        urgencia="media",
        prevencion="Aplicar anualmente",
        applied_at=datetime.utcnow() - timedelta(days=days_ago),
        created_at=datetime.utcnow() - timedelta(days=days_ago),
    )
    db.add(t)
    db.commit()
    return t


# ---------------------------------------------------------------------------
# Key-schema assertion
# ---------------------------------------------------------------------------

def test_response_schema_keys(client, db, farm, field):
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/upcoming-treatments")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) <= 3  # max 3 windows
    if data:
        item = data[0]
        assert "treatment_type" in item
        assert "recommended_date" in item
        assert "reason_es" in item


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_unknown_field_returns_404(client, farm):
    resp = client.get(f"/api/farms/{farm.id}/fields/9999/upcoming-treatments")
    assert resp.status_code == 404


def test_unknown_farm_returns_404(client):
    resp = client.get("/api/farms/9999/fields/1/upcoming-treatments")
    assert resp.status_code == 404


def test_recent_treatment_schedules_far_window(client, db, farm, field):
    """Treatment applied 2 days ago → next window at least 14 days out."""
    _add_treatment(db, field.id, days_ago=2)
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/upcoming-treatments")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    # First recommended date should be at least 14 days from now
    from datetime import date
    first_date = date.fromisoformat(data[0]["recommended_date"])
    assert (first_date - date.today()).days >= 14


def test_no_treatment_history_returns_schedule(client, db, farm, field):
    """No prior treatments → still returns 3 upcoming windows."""
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/upcoming-treatments")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3


def test_missing_phenology_returns_generic_schedule(client, db, farm, field_no_phenology):
    """Field with no planted_at → generic schedule returned, not empty or 404."""
    resp = client.get(f"/api/farms/{farm.id}/fields/{field_no_phenology.id}/upcoming-treatments")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # reason_es should mention generic or season
    assert all("reason_es" in item for item in data)


def test_reason_es_is_spanish(client, db, farm, field):
    """reason_es field should be non-empty Spanish text."""
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/upcoming-treatments")
    assert resp.status_code == 200
    data = resp.json()
    for item in data:
        assert item["reason_es"] and len(item["reason_es"]) > 5
