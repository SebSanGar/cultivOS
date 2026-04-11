"""Tests for GET /api/farms/{farm_id}/regen-trajectory."""

from datetime import datetime

from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_farm(db, name="Rancho Prueba"):
    farm = Farm(name=name, state="Jalisco")
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id, name="Campo Uno", crop_type="maiz"):
    field = Field(farm_id=farm_id, name=name, crop_type=crop_type)
    db.add(field)
    db.commit()
    return field


def _make_health(db, field_id, score, month_dt):
    h = HealthScore(
        field_id=field_id,
        score=score,
        sources=["ndvi"],
        breakdown={},
        scored_at=month_dt,
    )
    db.add(h)
    db.commit()
    return h


def _make_treatment(db, field_id, organic, month_dt):
    t = TreatmentRecord(
        field_id=field_id,
        health_score_used=70.0,
        problema="Plaga",
        causa_probable="Humedad alta",
        tratamiento="Aplicar neem",
        costo_estimado_mxn=500,
        urgencia="media",
        prevencion="Rotacion de cultivos",
        organic=organic,
        created_at=month_dt,
    )
    db.add(t)
    db.commit()
    return t


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_response_keys_present(client, db):
    """Response contains required top-level keys."""
    farm = _make_farm(db)
    resp = client.get(f"/api/farms/{farm.id}/regen-trajectory")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "farm_id" in data
    assert "months" in data
    assert "trend" in data


def test_404_unknown_farm(client):
    """Unknown farm_id returns 404."""
    resp = client.get("/api/farms/99999/regen-trajectory")
    assert resp.status_code == 404


def test_empty_farm_returns_empty_months(client, db):
    """Farm with no health scores or treatments → months = [], trend = 'stable'."""
    farm = _make_farm(db)
    resp = client.get(f"/api/farms/{farm.id}/regen-trajectory")
    assert resp.status_code == 200
    data = resp.json()
    assert data["months"] == []
    assert data["trend"] == "stable"


def test_single_month_returns_stable(client, db):
    """Farm with data only in one month → trend = 'stable'."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    dt = datetime(2026, 3, 15)
    _make_health(db, field.id, score=70.0, month_dt=dt)
    _make_treatment(db, field.id, organic=True, month_dt=dt)

    resp = client.get(f"/api/farms/{farm.id}/regen-trajectory")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["months"]) == 1
    assert data["trend"] == "stable"


def test_month_entry_keys_present(client, db):
    """Each month entry has required keys."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _make_health(db, field.id, score=65.0, month_dt=datetime(2026, 2, 10))

    resp = client.get(f"/api/farms/{farm.id}/regen-trajectory")
    assert resp.status_code == 200
    month = resp.json()["months"][0]
    assert "month" in month           # e.g. "2026-02"
    assert "organic_treatment_pct" in month
    assert "avg_health_score" in month
    assert "treatment_count" in month
    assert "regen_score" in month


def test_organic_pct_computed_correctly(client, db):
    """2 organic + 1 non-organic treatment → organic_treatment_pct = 66.67."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    dt = datetime(2026, 1, 15)
    _make_treatment(db, field.id, organic=True, month_dt=dt)
    _make_treatment(db, field.id, organic=True, month_dt=dt)
    _make_treatment(db, field.id, organic=False, month_dt=dt)

    resp = client.get(f"/api/farms/{farm.id}/regen-trajectory")
    assert resp.status_code == 200
    month = resp.json()["months"][0]
    assert month["treatment_count"] == 3
    assert abs(month["organic_treatment_pct"] - 66.67) < 1.0


def test_regen_score_formula(client, db):
    """regen_score = organic_pct * 0.6 + avg_health_score * 0.4."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    dt = datetime(2026, 1, 20)
    _make_health(db, field.id, score=80.0, month_dt=dt)
    _make_treatment(db, field.id, organic=True, month_dt=dt)  # 100% organic

    resp = client.get(f"/api/farms/{farm.id}/regen-trajectory")
    assert resp.status_code == 200
    month = resp.json()["months"][0]
    expected = 100.0 * 0.6 + 80.0 * 0.4  # = 92.0
    assert abs(month["regen_score"] - expected) < 1.0


def test_improving_trend(client, db):
    """Last 3 months avg regen_score > first 3 months by >5 → improving."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    # First 3 months: low health + no organic treatments (regen ~20)
    for month in [1, 2, 3]:
        dt = datetime(2026, month, 15)
        _make_health(db, field.id, score=30.0, month_dt=dt)
        _make_treatment(db, field.id, organic=False, month_dt=dt)

    # Last 3 months: high health + fully organic (regen ~92)
    for month in [4, 5, 6]:
        dt = datetime(2026, month, 15)
        _make_health(db, field.id, score=85.0, month_dt=dt)
        _make_treatment(db, field.id, organic=True, month_dt=dt)

    resp = client.get(f"/api/farms/{farm.id}/regen-trajectory")
    assert resp.status_code == 200
    assert resp.json()["trend"] == "improving"


def test_declining_trend(client, db):
    """Last 3 months avg regen_score < first 3 months by >5 → declining."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    # First 3 months: high health + fully organic (regen ~92)
    for month in [1, 2, 3]:
        dt = datetime(2026, month, 15)
        _make_health(db, field.id, score=85.0, month_dt=dt)
        _make_treatment(db, field.id, organic=True, month_dt=dt)

    # Last 3 months: low health + no organic (regen ~12)
    for month in [4, 5, 6]:
        dt = datetime(2026, month, 15)
        _make_health(db, field.id, score=20.0, month_dt=dt)
        _make_treatment(db, field.id, organic=False, month_dt=dt)

    resp = client.get(f"/api/farms/{farm.id}/regen-trajectory")
    assert resp.status_code == 200
    assert resp.json()["trend"] == "declining"


def test_months_sorted_chronologically(client, db):
    """Months returned in ascending chronological order."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    _make_health(db, field.id, score=70.0, month_dt=datetime(2026, 3, 10))
    _make_health(db, field.id, score=60.0, month_dt=datetime(2026, 1, 5))
    _make_health(db, field.id, score=65.0, month_dt=datetime(2026, 2, 20))

    resp = client.get(f"/api/farms/{farm.id}/regen-trajectory")
    assert resp.status_code == 200
    months = [m["month"] for m in resp.json()["months"]]
    assert months == sorted(months)
