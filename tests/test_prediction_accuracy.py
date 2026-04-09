"""Tests for prediction accuracy tracker at /precision-ia."""

from datetime import datetime, timedelta

import pytest

from cultivos.db.models import (
    Farm,
    Field,
    HealthScore,
    PredictionSnapshot,
)


def _seed_predictions(db):
    """Seed prediction snapshots with some resolved (actual_value set)."""
    farm = Farm(name="Rancho Prediccion", state="Jalisco", total_hectares=50.0)
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Parcela Test", hectares=10.0, crop_type="maiz")
    db.add(field)
    db.flush()

    now = datetime.utcnow()

    # Yield predictions — 3 resolved, 1 pending
    db.add(PredictionSnapshot(
        field_id=field.id, prediction_type="yield",
        predicted_value=4500.0, actual_value=4200.0,
        predicted_at=now - timedelta(days=90), resolved_at=now - timedelta(days=5),
    ))
    db.add(PredictionSnapshot(
        field_id=field.id, prediction_type="yield",
        predicted_value=5000.0, actual_value=5100.0,
        predicted_at=now - timedelta(days=60), resolved_at=now - timedelta(days=3),
    ))
    db.add(PredictionSnapshot(
        field_id=field.id, prediction_type="yield",
        predicted_value=3000.0, actual_value=3600.0,
        predicted_at=now - timedelta(days=30), resolved_at=now - timedelta(days=1),
    ))
    db.add(PredictionSnapshot(
        field_id=field.id, prediction_type="yield",
        predicted_value=4800.0, actual_value=None,
        predicted_at=now - timedelta(days=10), resolved_at=None,
    ))

    # Health predictions — 2 resolved
    db.add(PredictionSnapshot(
        field_id=field.id, prediction_type="health",
        predicted_value=75.0, actual_value=72.0,
        predicted_at=now - timedelta(days=45), resolved_at=now - timedelta(days=2),
    ))
    db.add(PredictionSnapshot(
        field_id=field.id, prediction_type="health",
        predicted_value=60.0, actual_value=55.0,
        predicted_at=now - timedelta(days=20), resolved_at=now - timedelta(days=1),
    ))

    db.commit()
    return farm, field


# ── ORM Tests ────────────────────────────────────────────────


class TestPredictionSnapshotModel:
    """ORM model stores prediction data correctly."""

    def test_create_snapshot(self, db):
        farm = Farm(name="F", state="Jalisco", total_hectares=10.0)
        db.add(farm)
        db.flush()
        field = Field(farm_id=farm.id, name="P", hectares=5.0, crop_type="maiz")
        db.add(field)
        db.flush()

        snap = PredictionSnapshot(
            field_id=field.id, prediction_type="yield",
            predicted_value=4500.0, predicted_at=datetime.utcnow(),
        )
        db.add(snap)
        db.commit()
        assert snap.id is not None
        assert snap.actual_value is None
        assert snap.resolved_at is None

    def test_resolved_snapshot(self, db):
        farm = Farm(name="F", state="Jalisco", total_hectares=10.0)
        db.add(farm)
        db.flush()
        field = Field(farm_id=farm.id, name="P", hectares=5.0, crop_type="maiz")
        db.add(field)
        db.flush()

        now = datetime.utcnow()
        snap = PredictionSnapshot(
            field_id=field.id, prediction_type="health",
            predicted_value=80.0, actual_value=75.0,
            predicted_at=now - timedelta(days=30), resolved_at=now,
        )
        db.add(snap)
        db.commit()
        assert snap.actual_value == 75.0
        assert snap.resolved_at is not None


# ── API Tests ────────────────────────────────────────────────


class TestPredictionAccuracyAPI:
    """API returns accuracy metrics."""

    def test_endpoint_returns_200(self, client, db):
        _seed_predictions(db)
        resp = client.get("/api/intel/prediction-accuracy")
        assert resp.status_code == 200

    def test_returns_total_predictions(self, client, db):
        _seed_predictions(db)
        data = client.get("/api/intel/prediction-accuracy").json()
        assert data["total_predictions"] == 6

    def test_returns_resolved_count(self, client, db):
        _seed_predictions(db)
        data = client.get("/api/intel/prediction-accuracy").json()
        assert data["resolved"] == 5  # 3 yield + 2 health resolved

    def test_returns_pending_count(self, client, db):
        _seed_predictions(db)
        data = client.get("/api/intel/prediction-accuracy").json()
        assert data["pending"] == 1

    def test_returns_mape(self, client, db):
        _seed_predictions(db)
        data = client.get("/api/intel/prediction-accuracy").json()
        assert "mape" in data
        assert data["mape"] is not None
        assert data["mape"] > 0  # should be non-zero with our test data

    def test_mape_is_reasonable(self, client, db):
        """MAPE should be between 0 and 100 for reasonable predictions."""
        _seed_predictions(db)
        data = client.get("/api/intel/prediction-accuracy").json()
        assert 0 < data["mape"] < 50  # our test data has small errors

    def test_returns_by_type(self, client, db):
        _seed_predictions(db)
        data = client.get("/api/intel/prediction-accuracy").json()
        by_type = data["by_type"]
        assert "yield" in by_type
        assert "health" in by_type
        assert by_type["yield"]["resolved"] == 3
        assert by_type["health"]["resolved"] == 2

    def test_returns_recent_predictions(self, client, db):
        _seed_predictions(db)
        data = client.get("/api/intel/prediction-accuracy").json()
        assert "recent" in data
        assert len(data["recent"]) > 0
        pred = data["recent"][0]
        assert "prediction_type" in pred
        assert "predicted_value" in pred
        assert "predicted_at" in pred

    def test_empty_database_returns_zeros(self, client, db):
        resp = client.get("/api/intel/prediction-accuracy")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_predictions"] == 0
        assert data["resolved"] == 0
        assert data["mape"] is None
        assert data["recent"] == []

    def test_returns_accuracy_status(self, client, db):
        _seed_predictions(db)
        data = client.get("/api/intel/prediction-accuracy").json()
        assert "status" in data
        assert data["status"] in ("green", "yellow", "red")


# ── Page Load Tests ──────────────────────────────────────────


class TestPredictionAccuracyPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/precision-ia")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/precision-ia")
        assert "Precision" in resp.text or "precision" in resp.text

    def test_page_has_stats_strip(self, client):
        html = client.get("/precision-ia").text
        assert 'id="pred-stat-total"' in html
        assert 'id="pred-stat-resolved"' in html
        assert 'id="pred-stat-mape"' in html

    def test_page_has_chart_container(self, client):
        html = client.get("/precision-ia").text
        assert 'id="pred-chart"' in html

    def test_page_has_predictions_table(self, client):
        html = client.get("/precision-ia").text
        assert 'id="pred-recent"' in html

    def test_page_has_nav(self, client):
        html = client.get("/precision-ia").text
        assert "intel-nav" in html

    def test_page_has_js_script(self, client):
        html = client.get("/precision-ia").text
        assert "precision-ia.js" in html

    def test_page_has_spanish_labels(self, client):
        html = client.get("/precision-ia").text
        assert "Predicciones" in html or "predicciones" in html

    def test_page_has_footer(self, client):
        html = client.get("/precision-ia").text
        assert "cultivos-footer" in html

    def test_page_has_empty_state(self, client):
        html = client.get("/precision-ia").text
        assert 'id="pred-empty"' in html

    def test_page_has_by_type_section(self, client):
        html = client.get("/precision-ia").text
        assert 'id="pred-by-type"' in html

    def test_page_has_status_indicator(self, client):
        html = client.get("/precision-ia").text
        assert 'id="pred-status"' in html
