"""Tests for GET /api/farms/{farm_id}/fields/{field_id}/growth-report."""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Farm, Field, HealthScore
from cultivos.db.session import get_db


@pytest.fixture()
def client(db):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def farm(db):
    f = Farm(name="Granja Test", state="Jalisco", total_hectares=10.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def make_field(db, farm_id, crop_type="maiz", planted_at=None):
    """Helper: create a field with optional planting date."""
    field = Field(
        farm_id=farm_id,
        name="Lote A",
        crop_type=crop_type,
        hectares=5.0,
        planted_at=planted_at,
    )
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


def make_health(db, field_id, score):
    """Helper: seed a HealthScore record."""
    hs = HealthScore(
        field_id=field_id,
        score=score,
        scored_at=datetime.utcnow(),
        breakdown={},
    )
    db.add(hs)
    db.commit()
    return hs


# ── Schema key assertion ────────────────────────────────────────────────────

def test_response_keys_present(client, db, farm):
    """All required keys must be present in the response."""
    planted = datetime.utcnow() - timedelta(days=65)  # vegetativo stage for maiz
    field = make_field(db, farm.id, "maiz", planted_at=planted)
    make_health(db, field.id, 72.0)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/growth-report")
    assert r.status_code == 200
    body = r.json()
    for key in ("field_id", "crop_type", "current_stage", "expected_stage",
                "on_track", "health_vs_expected", "lag_days", "recommendations"):
        assert key in body, f"Missing key: {key}"


# ── On-track case ───────────────────────────────────────────────────────────

def test_on_track_crop(client, db, farm):
    """A healthy crop at floracion returns on_track=True and lag_days=0."""
    # maiz floracion: days 55-80 → plant 70 days ago = mid-floracion
    planted = datetime.utcnow() - timedelta(days=70)
    field = make_field(db, farm.id, "maiz", planted_at=planted)
    # health=78 exactly matches floracion baseline (expected=78) → ratio=1.0
    make_health(db, field.id, 78.0)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/growth-report")
    assert r.status_code == 200
    body = r.json()
    assert body["current_stage"] == "floracion"
    assert body["expected_stage"] == "floracion"
    assert body["on_track"] is True
    assert body["lag_days"] == 0
    assert body["health_vs_expected"] == pytest.approx(1.0, abs=0.05)


# ── Behind case ─────────────────────────────────────────────────────────────

def test_crop_behind_returns_lag_days(client, db, farm):
    """A low-health crop at floracion returns on_track=False and lag_days>0."""
    planted = datetime.utcnow() - timedelta(days=70)
    field = make_field(db, farm.id, "maiz", planted_at=planted)
    # health=50 vs expected=78 → ratio ≈ 0.64 → behind
    make_health(db, field.id, 50.0)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/growth-report")
    assert r.status_code == 200
    body = r.json()
    assert body["on_track"] is False
    assert body["lag_days"] > 0
    assert body["health_vs_expected"] == pytest.approx(50.0 / 78.0, abs=0.05)


# ── No planted_at fallback ──────────────────────────────────────────────────

def test_no_planting_date_graceful_fallback(client, db, farm):
    """When planted_at is None, stage fields are None and lag_days=0."""
    field = make_field(db, farm.id, "maiz", planted_at=None)
    make_health(db, field.id, 65.0)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/growth-report")
    assert r.status_code == 200
    body = r.json()
    assert body["current_stage"] is None
    assert body["expected_stage"] is None
    assert body["on_track"] is None
    assert body["lag_days"] == 0


# ── No health data fallback ─────────────────────────────────────────────────

def test_no_health_data_graceful(client, db, farm):
    """When no HealthScore exists, health_vs_expected and on_track are None."""
    planted = datetime.utcnow() - timedelta(days=40)
    field = make_field(db, farm.id, "maiz", planted_at=planted)
    # No health score seeded

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/growth-report")
    assert r.status_code == 200
    body = r.json()
    assert body["health_vs_expected"] is None
    assert body["on_track"] is None
    assert any("Sin datos" in rec or "evaluación" in rec for rec in body["recommendations"])


# ── 404 cases ───────────────────────────────────────────────────────────────

def test_unknown_farm_returns_404(client, db):
    """Unknown farm_id → 404."""
    r = client.get("/api/farms/99999/fields/1/growth-report")
    assert r.status_code == 404


def test_unknown_field_returns_404(client, db, farm):
    """Unknown field_id for a valid farm → 404."""
    r = client.get(f"/api/farms/{farm.id}/fields/99999/growth-report")
    assert r.status_code == 404


# ── Recommendations content ─────────────────────────────────────────────────

def test_low_health_includes_organic_recommendation(client, db, farm):
    """Severely lagging crop (ratio < 0.7) includes organic fertilizer recommendation."""
    planted = datetime.utcnow() - timedelta(days=70)
    field = make_field(db, farm.id, "maiz", planted_at=planted)
    make_health(db, field.id, 40.0)  # 40/78 ≈ 0.51 < 0.7

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/growth-report")
    assert r.status_code == 200
    body = r.json()
    recs = " ".join(body["recommendations"])
    assert "orgánico" in recs or "abono" in recs
