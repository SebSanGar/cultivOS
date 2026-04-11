"""Tests for GET /api/intel/farms/compare?farm_ids=1,2,3."""

from datetime import datetime
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def farm_a(db):
    from cultivos.db.models import Farm
    f = Farm(name="Rancho A", state="Jalisco", total_hectares=20.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@pytest.fixture
def farm_b(db):
    from cultivos.db.models import Farm
    f = Farm(name="Rancho B", state="Jalisco", total_hectares=10.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@pytest.fixture
def field_a(db, farm_a):
    from cultivos.db.models import Field
    f = Field(farm_id=farm_a.id, name="Parcela 1", crop_type="maiz", hectares=20.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@pytest.fixture
def field_b(db, farm_b):
    from cultivos.db.models import Field
    f = Field(farm_id=farm_b.id, name="Parcela 2", crop_type="frijol", hectares=10.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def _add_health(db, field_id, score):
    from cultivos.db.models import HealthScore
    hs = HealthScore(
        field_id=field_id,
        score=score,
        scored_at=datetime.utcnow(),
        ndvi_mean=0.6,
    )
    db.add(hs)
    db.commit()


def _add_treatment(db, field_id, organic=True):
    from cultivos.db.models import TreatmentRecord
    t = TreatmentRecord(
        field_id=field_id,
        health_score_used=50.0,
        problema="Baja fertilidad",
        causa_probable="Suelo degradado",
        tratamiento="compost",
        costo_estimado_mxn=500,
        urgencia="media",
        prevencion="Aplicar anualmente",
        organic=organic,
    )
    db.add(t)
    db.commit()


# ---------------------------------------------------------------------------
# Key-schema assertion
# ---------------------------------------------------------------------------

def test_response_schema_keys(client, db, farm_a, field_a):
    _add_health(db, field_a.id, 75.0)
    resp = client.get(f"/api/intel/farms/compare?farm_ids={farm_a.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "farms" in data
    assert isinstance(data["farms"], list)
    row = data["farms"][0]
    assert "farm_id" in row
    assert "farm_name" in row
    assert "avg_health" in row
    assert "total_hectares" in row
    assert "treatment_count" in row
    assert "co2e_sequestered" in row
    assert "organic_pct" in row
    assert "certification_readiness" in row


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_two_farms_compared(client, db, farm_a, farm_b, field_a, field_b):
    _add_health(db, field_a.id, 80.0)
    _add_health(db, field_b.id, 40.0)

    resp = client.get(f"/api/intel/farms/compare?farm_ids={farm_a.id},{farm_b.id}")
    assert resp.status_code == 200
    data = resp.json()

    assert len(data["farms"]) == 2
    ids = [row["farm_id"] for row in data["farms"]]
    assert farm_a.id in ids
    assert farm_b.id in ids


def test_unknown_farm_id_returns_null_row(client, db, farm_a, field_a):
    """Unknown farm ID returns a null row — does NOT raise 404."""
    _add_health(db, field_a.id, 70.0)

    resp = client.get(f"/api/intel/farms/compare?farm_ids={farm_a.id},9999")
    assert resp.status_code == 200
    data = resp.json()

    assert len(data["farms"]) == 2
    null_row = next(r for r in data["farms"] if r["farm_id"] == 9999)
    assert null_row["farm_name"] is None
    assert null_row["avg_health"] is None


def test_empty_farm_ids_returns_empty_list(client):
    resp = client.get("/api/intel/farms/compare?farm_ids=")
    assert resp.status_code == 200
    data = resp.json()
    assert data["farms"] == []


def test_organic_pct_only_organic_treatments(client, db, farm_a, field_a):
    """Farm with all organic treatments should have organic_pct = 100.0."""
    _add_treatment(db, field_a.id, organic=True)
    _add_treatment(db, field_a.id, organic=True)

    resp = client.get(f"/api/intel/farms/compare?farm_ids={farm_a.id}")
    assert resp.status_code == 200
    data = resp.json()

    row = data["farms"][0]
    assert row["organic_pct"] == pytest.approx(100.0, abs=0.1)


def test_organic_pct_mixed_treatments(client, db, farm_a, field_a):
    """Farm with 1 organic + 1 synthetic should have organic_pct = 50.0."""
    _add_treatment(db, field_a.id, organic=True)
    _add_treatment(db, field_a.id, organic=False)

    resp = client.get(f"/api/intel/farms/compare?farm_ids={farm_a.id}")
    assert resp.status_code == 200
    data = resp.json()

    row = data["farms"][0]
    assert row["organic_pct"] == pytest.approx(50.0, abs=0.1)


def test_certification_readiness_present(client, db, farm_a, field_a):
    resp = client.get(f"/api/intel/farms/compare?farm_ids={farm_a.id}")
    assert resp.status_code == 200
    data = resp.json()

    row = data["farms"][0]
    assert row["certification_readiness"] is not None
    assert 0.0 <= row["certification_readiness"] <= 100.0


def test_order_matches_input(client, db, farm_a, farm_b):
    """Response order must match farm_ids input order."""
    resp = client.get(f"/api/intel/farms/compare?farm_ids={farm_b.id},{farm_a.id}")
    assert resp.status_code == 200
    data = resp.json()

    assert len(data["farms"]) == 2
    assert data["farms"][0]["farm_id"] == farm_b.id
    assert data["farms"][1]["farm_id"] == farm_a.id
