"""Tests for GET /api/intel/farms/compare — side-by-side farm comparison endpoint."""

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


def _add_field(db, farm_id, name="Parcela 1", hectares=5.0, crop_type="maiz"):
    from cultivos.db.models import Field
    fld = Field(farm_id=farm_id, name=name, crop_type=crop_type, hectares=hectares)
    db.add(fld)
    db.commit()
    db.refresh(fld)
    return fld


def _add_health(db, field_id, score):
    from cultivos.db.models import HealthScore
    hs = HealthScore(field_id=field_id, score=score, ndvi_mean=0.6)
    db.add(hs)
    db.commit()
    return hs


def _add_treatment(db, field_id, organic=True):
    from cultivos.db.models import TreatmentRecord
    t = TreatmentRecord(
        field_id=field_id,
        tratamiento="Aplicar composta",
        health_score_used=60.0,
        problema="sequia",
        causa_probable="falta de lluvia",
        urgencia="media",
        prevencion="Mulchear el suelo",
        organic=organic,
    )
    db.add(t)
    db.commit()
    return t


# ---------------------------------------------------------------------------
# Key-schema assertion
# ---------------------------------------------------------------------------

def test_response_schema_keys(client, db, farm_a):
    resp = client.get(f"/api/intel/farms/compare?farm_ids={farm_a.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "farms" in data
    assert isinstance(data["farms"], list)
    if data["farms"]:
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

def test_two_farms_compared(client, db, farm_a, farm_b):
    """Two farms returned in input order."""
    fld_a = _add_field(db, farm_a.id, "Parcela A", hectares=10.0)
    fld_b = _add_field(db, farm_b.id, "Parcela B", hectares=5.0)
    _add_health(db, fld_a.id, 80.0)
    _add_health(db, fld_b.id, 60.0)

    resp = client.get(f"/api/intel/farms/compare?farm_ids={farm_a.id},{farm_b.id}")
    assert resp.status_code == 200
    farms = resp.json()["farms"]
    assert len(farms) == 2
    assert farms[0]["farm_id"] == farm_a.id
    assert farms[1]["farm_id"] == farm_b.id
    assert farms[0]["farm_name"] == "Rancho A"
    assert farms[1]["farm_name"] == "Rancho B"


def test_unknown_farm_id_returns_null_row(client, db, farm_a):
    """Unknown farm ID returns null row (farm_name=None), not 404."""
    resp = client.get(f"/api/intel/farms/compare?farm_ids={farm_a.id},9999")
    assert resp.status_code == 200
    farms = resp.json()["farms"]
    assert len(farms) == 2
    null_row = next(f for f in farms if f["farm_id"] == 9999)
    assert null_row["farm_name"] is None
    assert null_row["avg_health"] is None


def test_empty_farm_ids_returns_empty_list(client, db):
    """Empty farm_ids param returns empty farms list."""
    resp = client.get("/api/intel/farms/compare?farm_ids=")
    assert resp.status_code == 200
    assert resp.json()["farms"] == []


def test_avg_health_correct(client, db, farm_a):
    """avg_health is the average of latest health scores across all fields."""
    fld1 = _add_field(db, farm_a.id, "P1", hectares=5.0)
    fld2 = _add_field(db, farm_a.id, "P2", hectares=5.0)
    _add_health(db, fld1.id, 80.0)
    _add_health(db, fld2.id, 60.0)

    resp = client.get(f"/api/intel/farms/compare?farm_ids={farm_a.id}")
    assert resp.status_code == 200
    row = resp.json()["farms"][0]
    assert row["avg_health"] == pytest.approx(70.0, abs=0.1)


def test_organic_pct_only_organic(client, db, farm_a):
    """organic_pct = 100 when all treatments are organic."""
    fld = _add_field(db, farm_a.id, "P1", hectares=5.0)
    _add_treatment(db, fld.id, organic=True)
    _add_treatment(db, fld.id, organic=True)

    resp = client.get(f"/api/intel/farms/compare?farm_ids={farm_a.id}")
    assert resp.status_code == 200
    row = resp.json()["farms"][0]
    assert row["organic_pct"] == pytest.approx(100.0, abs=0.1)
