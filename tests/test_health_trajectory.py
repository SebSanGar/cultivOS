"""Tests for GET /api/farms/{farm_id}/fields/{field_id}/health/trajectory endpoint."""

from datetime import datetime, timedelta

import pytest

from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord
from cultivos.services.crop.health import compute_health_trajectory


# --- Pure function tests ---


class TestComputeHealthTrajectory:
    """Test the pure compute_health_trajectory function."""

    def test_improving_trend(self):
        """Scores 40→50→60→70→80 should yield improving trend."""
        base = datetime(2026, 1, 1)
        health = [
            {"id": i, "score": 40.0 + i * 10, "scored_at": base + timedelta(days=i * 7)}
            for i in range(5)
        ]
        result = compute_health_trajectory(health, [])
        assert result["trend"] == "improving"
        assert result["rate_of_change"] > 0
        assert result["current_score"] == 80.0
        assert result["score_range"] == {"min": 40.0, "max": 80.0}
        assert result["data_points"] == 5

    def test_declining_trend(self):
        """Scores 80→70→60→50→40 should yield declining trend."""
        base = datetime(2026, 1, 1)
        health = [
            {"id": i, "score": 80.0 - i * 10, "scored_at": base + timedelta(days=i * 7)}
            for i in range(5)
        ]
        result = compute_health_trajectory(health, [])
        assert result["trend"] == "declining"
        assert result["rate_of_change"] < 0

    def test_stable_trend(self):
        """Scores all around 60 should yield stable trend."""
        base = datetime(2026, 1, 1)
        health = [
            {"id": i, "score": 60.0 + (i % 2), "scored_at": base + timedelta(days=i * 7)}
            for i in range(5)
        ]
        result = compute_health_trajectory(health, [])
        assert result["trend"] == "stable"

    def test_insufficient_data(self):
        """Fewer than 3 scores yields insufficient_data."""
        base = datetime(2026, 1, 1)
        health = [
            {"id": 1, "score": 50.0, "scored_at": base},
            {"id": 2, "score": 55.0, "scored_at": base + timedelta(days=7)},
        ]
        result = compute_health_trajectory(health, [])
        assert result["trend"] == "insufficient_data"
        assert result["data_points"] == 2

    def test_empty_scores(self):
        """No health scores yields insufficient_data with null current_score."""
        result = compute_health_trajectory([], [])
        assert result["trend"] == "insufficient_data"
        assert result["current_score"] is None
        assert result["data_points"] == 0

    def test_treatment_link_computed(self):
        """Treatment applied between two health scores produces a treatment link."""
        base = datetime(2026, 1, 1)
        health = [
            {"id": 1, "score": 40.0, "scored_at": base},
            {"id": 2, "score": 45.0, "scored_at": base + timedelta(days=7)},
            {"id": 3, "score": 65.0, "scored_at": base + timedelta(days=14)},
            {"id": 4, "score": 70.0, "scored_at": base + timedelta(days=21)},
        ]
        treatments = [
            {
                "id": 10,
                "tratamiento": "Composta de lombriz",
                "problema": "Bajo vigor",
                "applied_at": base + timedelta(days=10),
            }
        ]
        result = compute_health_trajectory(health, treatments)
        assert len(result["treatment_links"]) == 1
        link = result["treatment_links"][0]
        assert link["treatment_id"] == 10
        assert link["health_before"] == 45.0  # last score before applied_at
        assert link["health_after"] == 65.0  # first score after applied_at
        assert link["delta"] == 20.0

    def test_treatment_without_applied_at_excluded(self):
        """Treatments with no applied_at are excluded from links."""
        base = datetime(2026, 1, 1)
        health = [
            {"id": i, "score": 50.0 + i * 5, "scored_at": base + timedelta(days=i * 7)}
            for i in range(4)
        ]
        treatments = [
            {"id": 10, "tratamiento": "Neem", "problema": "Plagas", "applied_at": None}
        ]
        result = compute_health_trajectory(health, treatments)
        assert len(result["treatment_links"]) == 0

    def test_projection_clamped(self):
        """Projection should be clamped between 0 and 100."""
        base = datetime(2026, 1, 1)
        health = [
            {"id": i, "score": 85.0 + i * 5, "scored_at": base + timedelta(days=i * 7)}
            for i in range(5)
        ]
        result = compute_health_trajectory(health, [])
        assert result["projection"] is not None
        assert 0.0 <= result["projection"] <= 100.0


# --- API endpoint tests ---


class TestHealthTrajectoryAPI:
    """Test the GET /api/farms/{farm_id}/fields/{field_id}/health/trajectory endpoint."""

    def _seed_farm_field(self, db):
        farm = Farm(name="Rancho Test", state="Jalisco", total_hectares=50.0)
        db.add(farm)
        db.flush()
        field = Field(farm_id=farm.id, name="Parcela A", hectares=10.0, crop_type="maiz")
        db.add(field)
        db.flush()
        return farm.id, field.id

    def _seed_health_scores(self, db, field_id, scores_data):
        for s in scores_data:
            hs = HealthScore(
                field_id=field_id,
                score=s["score"],
                trend="stable",
                sources=["ndvi"],
                breakdown={"ndvi": s["score"]},
                scored_at=s["scored_at"],
            )
            db.add(hs)
        db.flush()

    def _seed_treatments(self, db, field_id, treatments_data):
        for t in treatments_data:
            tr = TreatmentRecord(
                field_id=field_id,
                health_score_used=50.0,
                problema=t["problema"],
                causa_probable="Test",
                tratamiento=t["tratamiento"],
                costo_estimado_mxn=100,
                urgencia="media",
                prevencion="Test prevention",
                applied_at=t.get("applied_at"),
            )
            db.add(tr)
        db.flush()

    def test_trajectory_returns_200(self, client, db):
        farm_id, field_id = self._seed_farm_field(db)
        base = datetime(2026, 1, 1)
        self._seed_health_scores(db, field_id, [
            {"score": 40.0, "scored_at": base},
            {"score": 50.0, "scored_at": base + timedelta(days=7)},
            {"score": 60.0, "scored_at": base + timedelta(days=14)},
            {"score": 70.0, "scored_at": base + timedelta(days=21)},
        ])
        db.commit()
        resp = client.get(f"/api/farms/{farm_id}/fields/{field_id}/health/trajectory")
        assert resp.status_code == 200
        data = resp.json()
        assert data["trend"] == "improving"
        assert data["field_id"] == field_id
        assert data["data_points"] == 4

    def test_trajectory_with_treatment_links(self, client, db):
        farm_id, field_id = self._seed_farm_field(db)
        base = datetime(2026, 1, 1)
        self._seed_health_scores(db, field_id, [
            {"score": 40.0, "scored_at": base},
            {"score": 42.0, "scored_at": base + timedelta(days=7)},
            {"score": 65.0, "scored_at": base + timedelta(days=14)},
            {"score": 70.0, "scored_at": base + timedelta(days=21)},
        ])
        self._seed_treatments(db, field_id, [
            {
                "tratamiento": "Composta de lombriz",
                "problema": "Bajo vigor",
                "applied_at": base + timedelta(days=10),
            }
        ])
        db.commit()
        resp = client.get(f"/api/farms/{farm_id}/fields/{field_id}/health/trajectory")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["treatment_links"]) == 1
        assert data["treatment_links"][0]["delta"] > 0

    def test_trajectory_no_scores_returns_empty(self, client, db):
        farm_id, field_id = self._seed_farm_field(db)
        db.commit()
        resp = client.get(f"/api/farms/{farm_id}/fields/{field_id}/health/trajectory")
        assert resp.status_code == 200
        data = resp.json()
        assert data["trend"] == "insufficient_data"
        assert data["current_score"] is None
        assert data["scores"] == []

    def test_trajectory_farm_not_found(self, client, db):
        resp = client.get("/api/farms/999/fields/1/health/trajectory")
        assert resp.status_code == 404

    def test_trajectory_field_not_found(self, client, db):
        farm = Farm(name="Rancho Test", state="Jalisco", total_hectares=50.0)
        db.add(farm)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/999/health/trajectory")
        assert resp.status_code == 404

    def test_trajectory_includes_scores_list(self, client, db):
        farm_id, field_id = self._seed_farm_field(db)
        base = datetime(2026, 1, 1)
        self._seed_health_scores(db, field_id, [
            {"score": 50.0, "scored_at": base},
            {"score": 55.0, "scored_at": base + timedelta(days=7)},
            {"score": 60.0, "scored_at": base + timedelta(days=14)},
        ])
        db.commit()
        resp = client.get(f"/api/farms/{farm_id}/fields/{field_id}/health/trajectory")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["scores"]) == 3
        assert data["scores"][0]["score"] == 50.0
