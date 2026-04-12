"""Tests for cooperative annual report aggregate.

GET /api/cooperatives/{coop_id}/annual-report?year=
Composes per-farm compute_annual_report across all member farms.
"""

from datetime import datetime

import pytest


@pytest.fixture
def coop(db):
    from cultivos.db.models import Cooperative
    c = Cooperative(name="Cooperativa Anual", state="Jalisco")
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def _farm(db, coop, name="Rancho"):
    from cultivos.db.models import Farm
    f = Farm(name=name, state="Jalisco", total_hectares=50.0, cooperative_id=coop.id)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def _field(db, farm, name="Parcela", crop_type="maiz"):
    from cultivos.db.models import Field
    fld = Field(farm_id=farm.id, name=name, crop_type=crop_type, hectares=5.0)
    db.add(fld)
    db.commit()
    db.refresh(fld)
    return fld


def _health(db, field, score, at):
    from cultivos.db.models import HealthScore
    h = HealthScore(
        field_id=field.id, score=score, sources=["ndvi"], breakdown={}, scored_at=at
    )
    db.add(h)
    db.commit()
    return h


def _treatment(db, field, organic=True, at=None):
    from cultivos.db.models import TreatmentRecord
    t = TreatmentRecord(
        field_id=field.id,
        health_score_used=60.0,
        problema="plaga",
        causa_probable="humedad",
        tratamiento="neem",
        costo_estimado_mxn=100,
        urgencia="media",
        prevencion="rotacion",
        organic=organic,
        applied_at=at or datetime(2025, 6, 1),
    )
    db.add(t)
    db.commit()
    return t


def test_coop_annual_report_basic(client, db, coop):
    """Two farms with health improvements aggregate correctly."""
    f1 = _farm(db, coop, name="Rancho A")
    f2 = _farm(db, coop, name="Rancho B")
    fa = _field(db, f1, name="A1")
    fb = _field(db, f2, name="B1")
    _health(db, fa, 50.0, datetime(2025, 2, 1))
    _health(db, fa, 70.0, datetime(2025, 10, 1))
    _health(db, fb, 60.0, datetime(2025, 3, 1))
    _health(db, fb, 80.0, datetime(2025, 11, 1))
    _treatment(db, fa, organic=True, at=datetime(2025, 6, 1))
    _treatment(db, fb, organic=True, at=datetime(2025, 7, 1))

    resp = client.get(f"/api/cooperatives/{coop.id}/annual-report?year=2025")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cooperative_id"] == coop.id
    assert data["year"] == 2025
    assert data["total_farms"] == 2
    assert data["total_fields"] == 2
    # Both farms improved by 20 → avg_health_change = 20.0
    assert data["avg_health_change"] == pytest.approx(20.0, abs=0.01)
    assert data["total_treatments_applied"] == 2
    assert data["farms_improved_count"] == 2
    assert data["farms_total"] == 2
    assert data["best_farm"] is not None
    assert data["best_farm"]["health_delta"] == pytest.approx(20.0, abs=0.01)
    assert data["best_farm"]["farm_name"] in ("Rancho A", "Rancho B")


def test_coop_annual_report_year_param(client, db, coop):
    """Omitting year defaults to current year."""
    _farm(db, coop, name="Solo")
    resp = client.get(f"/api/cooperatives/{coop.id}/annual-report")
    assert resp.status_code == 200
    data = resp.json()
    assert data["year"] == datetime.utcnow().year


def test_coop_annual_report_empty_coop(client, db, coop):
    """Cooperative with no farms returns graceful empty."""
    resp = client.get(f"/api/cooperatives/{coop.id}/annual-report?year=2025")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cooperative_id"] == coop.id
    assert data["total_farms"] == 0
    assert data["total_fields"] == 0
    assert data["avg_health_change"] == 0.0
    assert data["total_co2e_sequestered_t"] == 0.0
    assert data["total_treatments_applied"] == 0
    assert data["best_farm"] is None
    assert data["farms_improved_count"] == 0
    assert data["farms_total"] == 0


def test_coop_annual_report_no_data(client, db, coop):
    """Farms with no health data → avg_health_change=0.0, best_farm=None."""
    f1 = _farm(db, coop, name="Vacio A")
    _field(db, f1, name="P1")
    resp = client.get(f"/api/cooperatives/{coop.id}/annual-report?year=2025")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_farms"] == 1
    assert data["total_fields"] == 1
    assert data["avg_health_change"] == 0.0
    assert data["best_farm"] is None
    assert data["farms_improved_count"] == 0


def test_coop_annual_report_best_farm(client, db, coop):
    """best_farm picks the farm with the highest health_delta."""
    f1 = _farm(db, coop, name="Mejor")
    f2 = _farm(db, coop, name="Peor")
    fa = _field(db, f1, name="A1")
    fb = _field(db, f2, name="B1")
    _health(db, fa, 40.0, datetime(2025, 1, 1))
    _health(db, fa, 90.0, datetime(2025, 12, 1))  # delta = +50
    _health(db, fb, 70.0, datetime(2025, 1, 1))
    _health(db, fb, 60.0, datetime(2025, 12, 1))  # delta = -10

    resp = client.get(f"/api/cooperatives/{coop.id}/annual-report?year=2025")
    data = resp.json()
    assert data["best_farm"]["farm_name"] == "Mejor"
    assert data["best_farm"]["health_delta"] == pytest.approx(50.0, abs=0.01)
    assert data["farms_improved_count"] == 1
    assert data["farms_total"] == 2
    # Mean of (+50, -10) = 20.0
    assert data["avg_health_change"] == pytest.approx(20.0, abs=0.01)


def test_coop_annual_report_404(client):
    """Unknown cooperative returns 404."""
    resp = client.get("/api/cooperatives/99999/annual-report?year=2025")
    assert resp.status_code == 404
