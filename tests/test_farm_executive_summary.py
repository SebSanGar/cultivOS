"""Tests for GET /api/farms/{farm_id}/executive-summary."""

from datetime import datetime, timedelta
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def farm(db):
    from cultivos.db.models import Farm
    f = Farm(name="Rancho Prueba", state="Jalisco", total_hectares=20.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@pytest.fixture
def field_a(db, farm):
    from cultivos.db.models import Field
    f = Field(farm_id=farm.id, name="Parcela A", crop_type="maiz", hectares=8.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@pytest.fixture
def field_b(db, farm):
    from cultivos.db.models import Field
    f = Field(farm_id=farm.id, name="Parcela B", crop_type="frijol", hectares=5.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def _add_health(db, field_id, score, days_ago=0):
    from cultivos.db.models import HealthScore
    hs = HealthScore(
        field_id=field_id,
        score=score,
        scored_at=datetime.utcnow() - timedelta(days=days_ago),
        ndvi_mean=0.6,
    )
    db.add(hs)
    db.commit()
    return hs


def _add_treatment(db, field_id, days_ago=0):
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
        created_at=datetime.utcnow() - timedelta(days=days_ago),
    )
    db.add(t)
    db.commit()
    return t


def _add_soil(db, field_id, organic_matter_pct=3.0):
    from cultivos.db.models import SoilAnalysis
    s = SoilAnalysis(
        field_id=field_id,
        organic_matter_pct=organic_matter_pct,
        sampled_at=datetime.utcnow(),
        ph=6.5,
    )
    db.add(s)
    db.commit()
    return s


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_unknown_farm_returns_404(client):
    resp = client.get("/api/farms/9999/executive-summary")
    assert resp.status_code == 404


def test_empty_farm_returns_zeros(client, farm):
    resp = client.get(f"/api/farms/{farm.id}/executive-summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["farm_id"] == farm.id
    assert data["farm_name"] == "Rancho Prueba"
    assert data["total_fields"] == 0
    assert data["total_hectares"] == 0
    assert data["avg_health"] is None
    assert data["total_treatments"] == 0
    assert data["active_alerts"] == 0
    assert data["total_co2e_tonnes"] == 0
    assert data["activity_30d"] == []


def test_populated_farm_aggregates_correctly(client, db, farm, field_a, field_b):
    # Add health scores
    _add_health(db, field_a.id, 80.0, days_ago=1)
    _add_health(db, field_b.id, 60.0, days_ago=2)

    # Add treatments (2 on field_a, 1 on field_b)
    _add_treatment(db, field_a.id, days_ago=5)
    _add_treatment(db, field_a.id, days_ago=10)
    _add_treatment(db, field_b.id, days_ago=3)

    # Add soil for CO2e
    _add_soil(db, field_a.id, organic_matter_pct=4.0)

    resp = client.get(f"/api/farms/{farm.id}/executive-summary")
    assert resp.status_code == 200
    data = resp.json()

    assert data["farm_id"] == farm.id
    assert data["total_fields"] == 2
    assert data["total_hectares"] == pytest.approx(13.0, abs=0.1)
    assert data["avg_health"] == pytest.approx(70.0, abs=0.5)
    assert data["total_treatments"] == 3
    assert data["total_co2e_tonnes"] > 0


def test_activity_30d_includes_recent_events(client, db, farm, field_a):
    _add_health(db, field_a.id, 75.0, days_ago=2)
    _add_treatment(db, field_a.id, days_ago=2)

    resp = client.get(f"/api/farms/{farm.id}/executive-summary")
    assert resp.status_code == 200
    data = resp.json()

    # At least one day should have activity
    assert len(data["activity_30d"]) >= 1
    total_events = sum(entry["count"] for entry in data["activity_30d"])
    assert total_events >= 2


def test_farm_scoped_not_global(client, db, farm):
    """Events from a different farm should not appear in this farm's summary."""
    from cultivos.db.models import Farm, Field
    other_farm = Farm(name="Otra Granja", state="Jalisco", total_hectares=5.0)
    db.add(other_farm)
    db.commit()
    db.refresh(other_farm)

    other_field = Field(farm_id=other_farm.id, name="Campo Ajeno", crop_type="maiz", hectares=3.0)
    db.add(other_field)
    db.commit()
    db.refresh(other_field)

    _add_treatment(db, other_field.id, days_ago=1)
    _add_health(db, other_field.id, 90.0, days_ago=1)

    resp = client.get(f"/api/farms/{farm.id}/executive-summary")
    assert resp.status_code == 200
    data = resp.json()
    # The empty farm should show zero treatments
    assert data["total_treatments"] == 0
    assert data["total_fields"] == 0
