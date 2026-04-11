"""Tests for GET /api/farms/{farm_id}/fields/{field_id}/health-volatility

Health score volatility index: std deviation of HealthScore over last 60 days.
Tiers: stable (<5 std dev), moderate (5-15), volatile (>15), insufficient_data (<2 scores).
"""

from datetime import datetime, timedelta

from cultivos.db.models import Farm, Field, HealthScore


# ── Helpers ────────────────────────────────────────────────────────────────────

def _farm(db):
    f = Farm(name="Test Farm", municipality="Guadalajara", total_hectares=10.0)
    db.add(f)
    db.commit()
    return f


def _field(db, farm_id, crop_type="maiz"):
    f = Field(farm_id=farm_id, name="Lote A", crop_type=crop_type, hectares=5.0)
    db.add(f)
    db.commit()
    return f


def _score(db, field_id, score, days_ago=0):
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
    r = client.get("/api/farms/99999/fields/99999/health-volatility")
    assert r.status_code == 404


def test_404_unknown_field(client, db):
    farm = _farm(db)
    r = client.get(f"/api/farms/{farm.id}/fields/99999/health-volatility")
    assert r.status_code == 404


def test_response_schema_keys(client, db):
    """Response has all required schema keys."""
    farm = _farm(db)
    field = _field(db, farm.id)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health-volatility")
    assert r.status_code == 200
    data = r.json()
    assert "field_id" in data
    assert "period_days" in data
    assert "score_count" in data
    assert "mean_health" in data
    assert "std_dev" in data
    assert "volatility_tier" in data
    assert "interpretation_es" in data


def test_no_scores_returns_insufficient_data(client, db):
    """Field with no HealthScore records returns insufficient_data tier."""
    farm = _farm(db)
    field = _field(db, farm.id)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health-volatility")
    assert r.status_code == 200
    data = r.json()
    assert data["volatility_tier"] == "insufficient_data"
    assert data["score_count"] == 0
    assert data["std_dev"] is None


def test_one_score_returns_insufficient_data(client, db):
    """Only one HealthScore record → insufficient_data (can't compute std dev)."""
    farm = _farm(db)
    field = _field(db, farm.id)
    _score(db, field.id, 75.0)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health-volatility")
    assert r.status_code == 200
    data = r.json()
    assert data["volatility_tier"] == "insufficient_data"
    assert data["score_count"] == 1


def test_identical_scores_are_stable(client, db):
    """Ten identical scores → std_dev=0, volatility_tier=stable."""
    farm = _farm(db)
    field = _field(db, farm.id)
    for i in range(10):
        _score(db, field.id, 80.0, days_ago=i * 2)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health-volatility")
    assert r.status_code == 200
    data = r.json()
    assert data["volatility_tier"] == "stable"
    assert data["std_dev"] == 0.0
    assert data["score_count"] == 10
    assert abs(data["mean_health"] - 80.0) < 0.01


def test_moderate_variance_tier(client, db):
    """Scores with std dev between 5-15 → moderate tier."""
    farm = _farm(db)
    field = _field(db, farm.id)
    # alternating 60 and 75 → std dev = 7.5
    for i in range(8):
        score = 60.0 if i % 2 == 0 else 75.0
        _score(db, field.id, score, days_ago=i * 5)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health-volatility")
    assert r.status_code == 200
    data = r.json()
    assert data["volatility_tier"] == "moderate"
    assert 5.0 <= data["std_dev"] <= 15.0


def test_high_variance_is_volatile(client, db):
    """Scores ranging 20-100 → std dev well above 15 → volatile tier."""
    farm = _farm(db)
    field = _field(db, farm.id)
    for i, score in enumerate([20.0, 100.0, 25.0, 95.0, 30.0, 90.0]):
        _score(db, field.id, score, days_ago=i * 7)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health-volatility")
    assert r.status_code == 200
    data = r.json()
    assert data["volatility_tier"] == "volatile"
    assert data["std_dev"] > 15.0


def test_scores_outside_60_days_excluded(client, db):
    """Scores older than 60 days are excluded from the calculation."""
    farm = _farm(db)
    field = _field(db, farm.id)
    # 1 recent score + 1 old score
    _score(db, field.id, 80.0, days_ago=5)
    _score(db, field.id, 20.0, days_ago=70)  # outside 60-day window

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health-volatility")
    assert r.status_code == 200
    data = r.json()
    # Only 1 score in window → insufficient_data
    assert data["score_count"] == 1
    assert data["volatility_tier"] == "insufficient_data"


def test_period_days_is_60(client, db):
    """Response always reports period_days=60."""
    farm = _farm(db)
    field = _field(db, farm.id)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health-volatility")
    assert r.status_code == 200
    assert r.json()["period_days"] == 60


def test_field_id_in_response(client, db):
    """field_id in response matches the queried field."""
    farm = _farm(db)
    field = _field(db, farm.id)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health-volatility")
    assert r.status_code == 200
    assert r.json()["field_id"] == field.id
