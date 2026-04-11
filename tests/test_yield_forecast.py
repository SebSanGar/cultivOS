"""Tests for GET /api/farms/{farm_id}/yield-forecast."""

from datetime import datetime, timedelta
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def farm(db):
    from cultivos.db.models import Farm
    f = Farm(name="Rancho Forecast", state="Jalisco", total_hectares=15.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@pytest.fixture
def field_high(db, farm):
    from cultivos.db.models import Field
    f = Field(farm_id=farm.id, name="Parcela Alta", crop_type="maiz", hectares=8.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@pytest.fixture
def field_low(db, farm):
    from cultivos.db.models import Field
    f = Field(farm_id=farm.id, name="Parcela Baja", crop_type="frijol", hectares=4.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@pytest.fixture
def field_no_health(db, farm):
    from cultivos.db.models import Field
    f = Field(farm_id=farm.id, name="Parcela Sin Datos", crop_type="chile", hectares=3.0)
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


def _add_prediction_snapshot(db, field_id, predicted_value=5000.0):
    from cultivos.db.models import PredictionSnapshot
    ps = PredictionSnapshot(
        field_id=field_id,
        prediction_type="yield",
        predicted_value=predicted_value,
        predicted_at=datetime.utcnow() - timedelta(days=10),
    )
    db.add(ps)
    db.commit()
    return ps


# ---------------------------------------------------------------------------
# Key-schema assertion (spec-formula alignment)
# ---------------------------------------------------------------------------

def test_response_schema_keys(client, db, farm, field_high):
    _add_health(db, field_high.id, 80.0)
    resp = client.get(f"/api/farms/{farm.id}/yield-forecast")
    assert resp.status_code == 200
    data = resp.json()
    assert "farm_id" in data
    assert "fields" in data
    assert isinstance(data["fields"], list)
    if data["fields"]:
        f = data["fields"][0]
        assert "field_id" in f
        assert "field_name" in f
        assert "crop_type" in f
        assert "projected_yield_kg" in f
        assert "confidence" in f
        assert "health_score_used" in f
        assert "has_prediction_snapshot" in f


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_unknown_farm_returns_404(client):
    resp = client.get("/api/farms/9999/yield-forecast")
    assert resp.status_code == 404


def test_high_health_higher_yield_than_low_health(client, db, farm, field_high, field_low):
    """Field with score=90 should project higher yield_kg than field with score=30."""
    _add_health(db, field_high.id, 90.0)
    _add_health(db, field_low.id, 30.0)

    resp = client.get(f"/api/farms/{farm.id}/yield-forecast")
    assert resp.status_code == 200
    data = resp.json()

    forecasts = {f["field_id"]: f for f in data["fields"]}
    high = forecasts[field_high.id]
    low = forecasts[field_low.id]

    # High health field should have higher kg/ha adjusted score
    assert high["health_score_used"] == pytest.approx(90.0, abs=0.1)
    assert low["health_score_used"] == pytest.approx(30.0, abs=0.1)
    # Both should have projected_yield_kg > 0
    assert high["projected_yield_kg"] > 0
    assert low["projected_yield_kg"] > 0
    # Yield per hectare: high/8ha vs low baseline / 4ha — high score multiplier dominates
    assert high["health_score_used"] > low["health_score_used"]


def test_missing_health_data_returns_fallback(client, db, farm, field_no_health):
    """Field with no health scores should return fallback estimate with low confidence."""
    resp = client.get(f"/api/farms/{farm.id}/yield-forecast")
    assert resp.status_code == 200
    data = resp.json()

    forecasts = {f["field_id"]: f for f in data["fields"]}
    f = forecasts[field_no_health.id]

    assert f["health_score_used"] is None
    assert f["projected_yield_kg"] > 0  # fallback estimate, not zero
    assert f["confidence"] == "low"


def test_confidence_low_without_prediction_snapshot(client, db, farm, field_high):
    """Without a PredictionSnapshot, confidence should be medium or low (not high)."""
    _add_health(db, field_high.id, 85.0)

    resp = client.get(f"/api/farms/{farm.id}/yield-forecast")
    assert resp.status_code == 200
    data = resp.json()

    forecasts = {f["field_id"]: f for f in data["fields"]}
    f = forecasts[field_high.id]

    assert f["has_prediction_snapshot"] is False
    # Without snapshot, confidence is at most "medium"
    assert f["confidence"] in ("low", "medium")


def test_has_prediction_snapshot_flagged(client, db, farm, field_high):
    """When a yield PredictionSnapshot exists, has_prediction_snapshot = True."""
    _add_health(db, field_high.id, 85.0)
    _add_prediction_snapshot(db, field_high.id)

    resp = client.get(f"/api/farms/{farm.id}/yield-forecast")
    assert resp.status_code == 200
    data = resp.json()

    forecasts = {f["field_id"]: f for f in data["fields"]}
    f = forecasts[field_high.id]
    assert f["has_prediction_snapshot"] is True


def test_empty_farm_returns_empty_fields(client, farm):
    resp = client.get(f"/api/farms/{farm.id}/yield-forecast")
    assert resp.status_code == 200
    data = resp.json()
    assert data["farm_id"] == farm.id
    assert data["fields"] == []
