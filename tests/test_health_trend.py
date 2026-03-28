"""Tests for historical health trend analysis endpoint."""

from datetime import datetime, timedelta

from cultivos.db.models import Farm, Field, HealthScore
from cultivos.services.crop.health import analyze_health_trend


# ── Pure service tests ──────────────────────────────────────────────────


class TestAnalyzeHealthTrend:
    """Test the pure analysis function."""

    def test_ascending_scores_classified_improving(self):
        scores = [30.0, 40.0, 50.0, 60.0, 70.0]
        dates = [datetime(2026, 1, i + 1) for i in range(5)]
        result = analyze_health_trend(scores, dates)
        assert result["trend"] == "improving"
        assert result["rate_of_change"] > 0

    def test_descending_scores_classified_declining(self):
        scores = [80.0, 70.0, 60.0, 50.0, 40.0]
        dates = [datetime(2026, 1, i + 1) for i in range(5)]
        result = analyze_health_trend(scores, dates)
        assert result["trend"] == "declining"
        assert result["rate_of_change"] < 0

    def test_flat_scores_classified_stable(self):
        scores = [60.0, 61.0, 59.0, 60.0, 60.5]
        dates = [datetime(2026, 1, i + 1) for i in range(5)]
        result = analyze_health_trend(scores, dates)
        assert result["trend"] == "stable"

    def test_fewer_than_3_points_insufficient(self):
        scores = [50.0, 55.0]
        dates = [datetime(2026, 1, 1), datetime(2026, 1, 2)]
        result = analyze_health_trend(scores, dates)
        assert result["trend"] == "insufficient_data"
        assert result["projection"] is None
        assert result["rate_of_change"] == 0.0

    def test_empty_scores(self):
        result = analyze_health_trend([], [])
        assert result["trend"] == "insufficient_data"
        assert result["projection"] is None
        assert result["data_points"] == 0

    def test_projection_within_20pct_ascending(self):
        """Linear ascending: projection should be close to actual next value."""
        # Scores: 20, 30, 40, 50, 60 — next should be ~70
        scores = [20.0, 30.0, 40.0, 50.0, 60.0]
        dates = [datetime(2026, 1, i + 1) for i in range(5)]
        result = analyze_health_trend(scores, dates)
        assert result["projection"] is not None
        # Projection of a perfect linear sequence should be ~70
        assert abs(result["projection"] - 70.0) <= 70.0 * 0.20

    def test_projection_within_20pct_descending(self):
        """Linear descending: projection should be close to actual next value."""
        scores = [90.0, 80.0, 70.0, 60.0, 50.0]
        dates = [datetime(2026, 1, i + 1) for i in range(5)]
        result = analyze_health_trend(scores, dates)
        assert result["projection"] is not None
        assert abs(result["projection"] - 40.0) <= 40.0 * 0.20

    def test_projection_clamped_0_100(self):
        """Projection should never exceed 0-100 range."""
        scores = [80.0, 85.0, 90.0, 95.0, 99.0]
        dates = [datetime(2026, 1, i + 1) for i in range(5)]
        result = analyze_health_trend(scores, dates)
        assert result["projection"] is not None
        assert 0 <= result["projection"] <= 100

    def test_rate_of_change_units(self):
        """Rate of change = slope per observation interval."""
        scores = [20.0, 30.0, 40.0, 50.0, 60.0]
        dates = [datetime(2026, 1, i + 1) for i in range(5)]
        result = analyze_health_trend(scores, dates)
        # Perfect +10/observation slope
        assert abs(result["rate_of_change"] - 10.0) < 0.5


# ── API endpoint tests ─────────────────────────────────────────────────


def _seed_health_scores(db, field_id, scores):
    """Helper to seed health score records."""
    base = datetime(2026, 1, 1)
    for i, score_val in enumerate(scores):
        hs = HealthScore(
            field_id=field_id,
            score=score_val,
            trend="stable",
            sources=["ndvi"],
            breakdown={"ndvi": score_val},
            scored_at=base + timedelta(days=i * 7),
        )
        db.add(hs)
    db.commit()


def test_health_trend_endpoint_improving(client, db):
    """Ascending scores return improving trend with projection."""
    farm = Farm(name="Test Farm", state="Jalisco", total_hectares=100)
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Field A", crop_type="maiz", hectares=10)
    db.add(field)
    db.flush()
    _seed_health_scores(db, field.id, [30, 40, 50, 60, 70])

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health/trend")
    assert resp.status_code == 200
    data = resp.json()
    assert data["trend"] == "improving"
    assert data["rate_of_change"] > 0
    assert data["projection"] is not None
    assert data["data_points"] == 5


def test_health_trend_endpoint_fewer_than_3(client, db):
    """Fewer than 3 scores returns insufficient_data."""
    farm = Farm(name="Test Farm", state="Jalisco", total_hectares=100)
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Field A", crop_type="maiz", hectares=10)
    db.add(field)
    db.flush()
    _seed_health_scores(db, field.id, [50, 55])

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health/trend")
    assert resp.status_code == 200
    data = resp.json()
    assert data["trend"] == "insufficient_data"
    assert data["projection"] is None
    assert data["data_points"] == 2


def test_health_trend_endpoint_no_scores(client, db):
    """No scores returns empty result."""
    farm = Farm(name="Test Farm", state="Jalisco", total_hectares=100)
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Field A", crop_type="maiz", hectares=10)
    db.add(field)
    db.flush()

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health/trend")
    assert resp.status_code == 200
    data = resp.json()
    assert data["trend"] == "insufficient_data"
    assert data["projection"] is None
    assert data["data_points"] == 0


def test_health_trend_invalid_field_404(client, db):
    """Non-existent field returns 404."""
    farm = Farm(name="Test Farm", state="Jalisco", total_hectares=100)
    db.add(farm)
    db.flush()

    resp = client.get(f"/api/farms/{farm.id}/fields/9999/health/trend")
    assert resp.status_code == 404


def test_health_trend_endpoint_declining(client, db):
    """Descending scores return declining trend."""
    farm = Farm(name="Test Farm", state="Jalisco", total_hectares=100)
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Field A", crop_type="maiz", hectares=10)
    db.add(field)
    db.flush()
    _seed_health_scores(db, field.id, [80, 70, 60, 50, 40])

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/health/trend")
    assert resp.status_code == 200
    data = resp.json()
    assert data["trend"] == "declining"
    assert data["rate_of_change"] < 0
    assert data["projection"] is not None
