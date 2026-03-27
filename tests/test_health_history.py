"""Tests for health score history + trend API."""

from datetime import datetime, timedelta

from cultivos.services.crop.health import compute_trend_from_history


# -- Pure function tests --


class TestComputeTrendFromHistory:
    def test_single_score_insufficient_data(self):
        """1 score returns trend='insufficient_data'."""
        result = compute_trend_from_history([75])
        assert result == "insufficient_data"

    def test_two_scores_insufficient_data(self):
        """2 scores still returns 'insufficient_data' (need 3+)."""
        result = compute_trend_from_history([60, 70])
        assert result == "insufficient_data"

    def test_declining_trend(self):
        """3+ scores with declining values returns trend='declining'."""
        result = compute_trend_from_history([80, 70, 55])
        assert result == "declining"

    def test_improving_trend(self):
        """3+ scores with improving values returns trend='improving'."""
        result = compute_trend_from_history([40, 55, 70])
        assert result == "improving"

    def test_stable_trend(self):
        """3+ scores with stable values returns trend='stable'."""
        result = compute_trend_from_history([70, 72, 69])
        assert result == "stable"

    def test_empty_list(self):
        result = compute_trend_from_history([])
        assert result == "insufficient_data"


# -- API integration tests --


class TestHealthHistoryAPI:
    def _seed_farm_field(self, db):
        from cultivos.db.models import Farm, Field
        farm = Farm(name="Test Farm", owner_name="Test Owner")
        db.add(farm)
        db.commit()
        db.refresh(farm)
        field = Field(farm_id=farm.id, name="Test Field", crop_type="maiz", hectares=5)
        db.add(field)
        db.commit()
        db.refresh(field)
        return farm.id, field.id

    def _seed_health_scores(self, db, field_id, scores):
        """Seed multiple health scores with ascending timestamps."""
        from cultivos.db.models import HealthScore
        base_time = datetime(2026, 1, 1)
        for i, score_val in enumerate(scores):
            record = HealthScore(
                field_id=field_id,
                score=score_val,
                trend="stable",
                sources=["ndvi"],
                breakdown={"ndvi": score_val},
                scored_at=base_time + timedelta(days=i),
            )
            db.add(record)
        db.commit()

    def test_health_history(self, client, db):
        """GET /health/history returns chronological list of scores."""
        fid, flid = self._seed_farm_field(db)
        self._seed_health_scores(db, flid, [60, 65, 70])
        resp = client.get(f"/api/farms/{fid}/fields/{flid}/health/history")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["scores"]) == 3
        # Chronological order (oldest first)
        assert data["scores"][0]["score"] == 60
        assert data["scores"][2]["score"] == 70

    def test_trend_calculation(self, client, db):
        """3+ scores with declining values returns trend='declining'."""
        fid, flid = self._seed_farm_field(db)
        self._seed_health_scores(db, flid, [80, 65, 50])
        resp = client.get(f"/api/farms/{fid}/fields/{flid}/health/history")
        assert resp.status_code == 200
        assert resp.json()["trend"] == "declining"

    def test_trend_improving(self, client, db):
        """3+ scores with improving values returns trend='improving'."""
        fid, flid = self._seed_farm_field(db)
        self._seed_health_scores(db, flid, [40, 55, 75])
        resp = client.get(f"/api/farms/{fid}/fields/{flid}/health/history")
        assert resp.status_code == 200
        assert resp.json()["trend"] == "improving"

    def test_single_score_no_trend(self, client, db):
        """1 score returns trend='insufficient_data'."""
        fid, flid = self._seed_farm_field(db)
        self._seed_health_scores(db, flid, [70])
        resp = client.get(f"/api/farms/{fid}/fields/{flid}/health/history")
        assert resp.status_code == 200
        assert resp.json()["trend"] == "insufficient_data"
