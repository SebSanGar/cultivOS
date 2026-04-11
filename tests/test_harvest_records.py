"""Tests for harvest record endpoints.

POST /api/farms/{farm_id}/fields/{field_id}/harvests
GET  /api/farms/{farm_id}/fields/{field_id}/harvests
"""

from datetime import datetime, timedelta
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def farm(db):
    from cultivos.db.models import Farm
    f = Farm(name="Rancho Cosecha", state="Jalisco", total_hectares=30.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@pytest.fixture
def field(db, farm):
    from cultivos.db.models import Field
    f = Field(farm_id=farm.id, name="Parcela Maiz", crop_type="maiz", hectares=10.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


# ---------------------------------------------------------------------------
# POST — create harvest record
# ---------------------------------------------------------------------------

def test_create_harvest_record(client, farm, field):
    """POST creates a HarvestRecord and returns 201."""
    payload = {
        "crop_type": "maiz",
        "harvest_date": "2026-04-01",
        "actual_yield_kg": 4500.0,
        "notes": "Buena cosecha, suelo bien hidratado",
    }
    resp = client.post(
        f"/api/farms/{farm.id}/fields/{field.id}/harvests",
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["field_id"] == field.id
    assert data["crop_type"] == "maiz"
    assert data["actual_yield_kg"] == pytest.approx(4500.0)
    assert "id" in data
    assert "harvest_date" in data


def test_create_harvest_unknown_farm(client, field):
    """POST with unknown farm_id returns 404."""
    payload = {
        "crop_type": "maiz",
        "harvest_date": "2026-04-01",
        "actual_yield_kg": 3000.0,
    }
    resp = client.post("/api/farms/9999/fields/1/harvests", json=payload)
    assert resp.status_code == 404


def test_create_harvest_unknown_field(client, farm):
    """POST with unknown field_id returns 404."""
    payload = {
        "crop_type": "maiz",
        "harvest_date": "2026-04-01",
        "actual_yield_kg": 3000.0,
    }
    resp = client.post(
        f"/api/farms/{farm.id}/fields/9999/harvests",
        json=payload,
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET — list harvest records
# ---------------------------------------------------------------------------

def test_list_harvests_empty(client, farm, field):
    """GET returns empty list when no harvests exist."""
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/harvests")
    assert resp.status_code == 200
    data = resp.json()
    assert data == []


def test_list_harvests_returns_records(client, db, farm, field):
    """GET returns all harvest records for the field."""
    from cultivos.db.models import HarvestRecord

    h1 = HarvestRecord(
        field_id=field.id,
        crop_type="maiz",
        harvest_date=datetime(2026, 3, 15),
        actual_yield_kg=4200.0,
        notes="Primera cosecha",
    )
    h2 = HarvestRecord(
        field_id=field.id,
        crop_type="maiz",
        harvest_date=datetime(2026, 4, 1),
        actual_yield_kg=3800.0,
    )
    db.add_all([h1, h2])
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/harvests")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    yields = {r["actual_yield_kg"] for r in data}
    assert 4200.0 in yields
    assert 3800.0 in yields


def test_list_harvests_unknown_field(client, farm):
    """GET with unknown field_id returns 404."""
    resp = client.get(f"/api/farms/{farm.id}/fields/9999/harvests")
    assert resp.status_code == 404


def test_harvest_scoped_to_field(client, db, farm, field):
    """Harvests from a different field are not included."""
    from cultivos.db.models import Field, HarvestRecord

    other_field = Field(farm_id=farm.id, name="Otra Parcela", crop_type="frijol", hectares=5.0)
    db.add(other_field)
    db.commit()
    db.refresh(other_field)

    h = HarvestRecord(
        field_id=other_field.id,
        crop_type="frijol",
        harvest_date=datetime(2026, 4, 1),
        actual_yield_kg=2000.0,
    )
    db.add(h)
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/harvests")
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# predicted_vs_actual — delta computation
# ---------------------------------------------------------------------------

def test_harvest_links_yield_prediction(client, db, farm, field):
    """POSTing a harvest updates PredictionSnapshot.actual_value for matching yield prediction."""
    from cultivos.db.models import PredictionSnapshot

    # Create a yield prediction for this field
    ps = PredictionSnapshot(
        field_id=field.id,
        prediction_type="yield",
        predicted_value=4000.0,
        predicted_at=datetime(2026, 3, 1),
    )
    db.add(ps)
    db.commit()
    db.refresh(ps)

    payload = {
        "crop_type": "maiz",
        "harvest_date": "2026-04-01",
        "actual_yield_kg": 4500.0,
    }
    resp = client.post(
        f"/api/farms/{farm.id}/fields/{field.id}/harvests",
        json=payload,
    )
    assert resp.status_code == 201

    # PredictionSnapshot.actual_value should now be updated
    db.refresh(ps)
    assert ps.actual_value == pytest.approx(4500.0)
    assert ps.resolved_at is not None


def test_harvest_list_includes_predicted_vs_actual(client, db, farm, field):
    """GET returns predicted_vs_actual_kg when a resolved prediction exists."""
    from cultivos.db.models import HarvestRecord, PredictionSnapshot

    ps = PredictionSnapshot(
        field_id=field.id,
        prediction_type="yield",
        predicted_value=3000.0,
        actual_value=3500.0,
        predicted_at=datetime(2026, 3, 1),
        resolved_at=datetime(2026, 4, 1),
    )
    db.add(ps)
    h = HarvestRecord(
        field_id=field.id,
        crop_type="maiz",
        harvest_date=datetime(2026, 4, 1),
        actual_yield_kg=3500.0,
    )
    db.add(h)
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/harvests")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    record = data[0]
    # predicted_vs_actual_kg = actual - predicted = 3500 - 3000 = 500
    assert record["predicted_vs_actual_kg"] == pytest.approx(500.0, abs=1.0)
