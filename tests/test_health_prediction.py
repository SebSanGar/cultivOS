"""Tests for #187 — Field 30-day health prediction.

GET /api/farms/{farm_id}/fields/{field_id}/health-prediction
Linear trend fit on last 60 days of HealthScore → project at +30 days.
"""

from datetime import datetime, timedelta

from cultivos.db.models import Farm, Field, HealthScore


# ── Helpers ──────────────────────────────────────────────────────────────────

def _farm(db, name="Rancho Prediccion"):
    f = Farm(name=name, municipality="Guadalajara", state="Jalisco", total_hectares=10.0)
    db.add(f)
    db.commit()
    return f


def _field(db, farm_id, crop_type="maiz"):
    f = Field(farm_id=farm_id, name="Lote Pred", crop_type=crop_type, hectares=5.0)
    db.add(f)
    db.commit()
    return f


def _add_health_scores(db, field_id, scores_with_days_ago):
    """Add HealthScore records. scores_with_days_ago = [(score, days_ago), ...]"""
    now = datetime.utcnow()
    for score_val, days_ago in scores_with_days_ago:
        hs = HealthScore(
            field_id=field_id,
            score=score_val,
            ndvi_mean=0.5,
            sources=["ndvi"],
            breakdown={},
            scored_at=now - timedelta(days=days_ago),
        )
        db.add(hs)
    db.commit()


# ── Tests ────────────────────────────────────────────────────────────────────

def test_404_unknown_farm(client, db):
    r = client.get("/api/farms/99999/fields/99999/health-prediction")
    assert r.status_code == 404


def test_404_unknown_field(client, db):
    farm = _farm(db)
    r = client.get(f"/api/farms/{farm.id}/fields/99999/health-prediction")
    assert r.status_code == 404


def test_response_schema_keys(client, db):
    """Response always has the expected keys."""
    farm = _farm(db)
    field = _field(db, farm.id)
    _add_health_scores(db, field.id, [(50.0, 5)])

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health-prediction")
    assert r.status_code == 200
    data = r.json()
    for key in ["field_id", "current_avg_health", "predicted_health_30d",
                "trend_direction", "confidence", "risk_flag", "data_points"]:
        assert key in data, f"Missing key: {key}"


def test_ascending_scores_predict_higher(client, db):
    """10 ascending scores → predicted > current avg."""
    farm = _farm(db)
    field = _field(db, farm.id)
    # Ascending: 40, 45, 50, 55, 60, 65, 70, 75, 80, 85 over last 50 days
    scores = [(40 + i * 5, 50 - i * 5) for i in range(10)]
    _add_health_scores(db, field.id, scores)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health-prediction")
    assert r.status_code == 200
    data = r.json()
    assert data["predicted_health_30d"] > data["current_avg_health"]
    assert data["trend_direction"] == "improving"
    assert data["confidence"] == "high"
    assert data["data_points"] == 10


def test_declining_scores_risk_flag(client, db):
    """Declining trend with low predicted score → risk_flag=True."""
    farm = _farm(db)
    field = _field(db, farm.id)
    # Declining from 50 to 20 over 50 days
    scores = [(50 - i * 3, 50 - i * 5) for i in range(10)]
    _add_health_scores(db, field.id, scores)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health-prediction")
    assert r.status_code == 200
    data = r.json()
    assert data["trend_direction"] == "declining"
    assert data["risk_flag"] is True
    assert data["predicted_health_30d"] < 40


def test_few_data_points_low_confidence(client, db):
    """<5 data points → confidence=low."""
    farm = _farm(db)
    field = _field(db, farm.id)
    _add_health_scores(db, field.id, [(60.0, 10), (65.0, 5), (70.0, 1)])

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health-prediction")
    assert r.status_code == 200
    data = r.json()
    assert data["confidence"] == "low"
    assert data["data_points"] == 3


def test_medium_confidence(client, db):
    """5-9 data points → confidence=medium."""
    farm = _farm(db)
    field = _field(db, farm.id)
    scores = [(50.0 + i, 30 - i * 5) for i in range(7)]
    _add_health_scores(db, field.id, scores)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health-prediction")
    assert r.status_code == 200
    data = r.json()
    assert data["confidence"] == "medium"
    assert data["data_points"] == 7


def test_predicted_clamped_0_100(client, db):
    """Prediction clamped to 0-100 even with extreme trends."""
    farm = _farm(db)
    field = _field(db, farm.id)
    # Very steep upward — should clamp at 100
    scores = [(10 + i * 20, 50 - i * 5) for i in range(10)]
    _add_health_scores(db, field.id, scores)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health-prediction")
    assert r.status_code == 200
    data = r.json()
    assert 0 <= data["predicted_health_30d"] <= 100


def test_stable_trend(client, db):
    """Flat scores → stable trend."""
    farm = _farm(db)
    field = _field(db, farm.id)
    scores = [(60.0, 50 - i * 5) for i in range(10)]
    _add_health_scores(db, field.id, scores)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health-prediction")
    assert r.status_code == 200
    data = r.json()
    assert data["trend_direction"] == "stable"
    assert data["risk_flag"] is False


def test_no_health_data_graceful(client, db):
    """Field with no health scores → graceful response with low confidence."""
    farm = _farm(db)
    field = _field(db, farm.id)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health-prediction")
    assert r.status_code == 200
    data = r.json()
    assert data["data_points"] == 0
    assert data["confidence"] == "low"
    assert data["trend_direction"] == "stable"
