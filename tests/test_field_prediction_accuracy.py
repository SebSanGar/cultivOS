"""Tests for per-field prediction accuracy endpoint.

GET /api/farms/{farm_id}/fields/{field_id}/predictions/accuracy
returns MAPE, resolved/pending counts, and per-type breakdown scoped to one field.
"""

from datetime import datetime, timedelta

from cultivos.db.models import Farm, Field, PredictionSnapshot


def _seed_two_fields_with_predictions(db):
    """Create two farms with two fields each, seeded with distinct prediction sets."""
    farm_a = Farm(name="Rancho A", state="Jalisco", total_hectares=50.0)
    farm_b = Farm(name="Rancho B", state="Jalisco", total_hectares=30.0)
    db.add_all([farm_a, farm_b])
    db.flush()

    field_a = Field(farm_id=farm_a.id, name="Parcela A1", hectares=10.0, crop_type="maiz")
    field_b = Field(farm_id=farm_b.id, name="Parcela B1", hectares=8.0, crop_type="frijol")
    db.add_all([field_a, field_b])
    db.flush()

    now = datetime.utcnow()

    # Field A: 2 resolved yield predictions with known errors + 1 pending
    # APE: |1000-900|/900*100 = 11.11; |2000-2200|/2200*100 = 9.09; mean ~10.1
    db.add(PredictionSnapshot(
        field_id=field_a.id, prediction_type="yield",
        predicted_value=1000.0, actual_value=900.0,
        predicted_at=now - timedelta(days=60), resolved_at=now - timedelta(days=5),
    ))
    db.add(PredictionSnapshot(
        field_id=field_a.id, prediction_type="yield",
        predicted_value=2000.0, actual_value=2200.0,
        predicted_at=now - timedelta(days=30), resolved_at=now - timedelta(days=2),
    ))
    db.add(PredictionSnapshot(
        field_id=field_a.id, prediction_type="yield",
        predicted_value=3000.0, actual_value=None,
        predicted_at=now - timedelta(days=10), resolved_at=None,
    ))
    # Field A: 1 resolved health prediction
    db.add(PredictionSnapshot(
        field_id=field_a.id, prediction_type="health",
        predicted_value=80.0, actual_value=78.0,
        predicted_at=now - timedelta(days=20), resolved_at=now - timedelta(days=1),
    ))

    # Field B: 1 resolved yield prediction — should NOT appear when querying field A
    db.add(PredictionSnapshot(
        field_id=field_b.id, prediction_type="yield",
        predicted_value=500.0, actual_value=100.0,  # MAPE 400%
        predicted_at=now - timedelta(days=15), resolved_at=now - timedelta(days=1),
    ))

    db.commit()
    return farm_a, field_a, farm_b, field_b


class TestFieldPredictionAccuracyEndpoint:

    def test_unknown_farm_returns_404(self, client):
        resp = client.get("/api/farms/9999/fields/1/predictions/accuracy")
        assert resp.status_code == 404

    def test_unknown_field_returns_404(self, client, db):
        farm = Farm(name="Solo", state="Jalisco", total_hectares=5.0)
        db.add(farm)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/9999/predictions/accuracy")
        assert resp.status_code == 404

    def test_field_from_wrong_farm_returns_404(self, client, db):
        farm_a, field_a, farm_b, field_b = _seed_two_fields_with_predictions(db)
        # field_b belongs to farm_b, not farm_a
        resp = client.get(f"/api/farms/{farm_a.id}/fields/{field_b.id}/predictions/accuracy")
        assert resp.status_code == 404

    def test_field_with_no_snapshots_returns_zero_totals(self, client, db):
        farm = Farm(name="Empty", state="Jalisco", total_hectares=5.0)
        db.add(farm)
        db.flush()
        field = Field(farm_id=farm.id, name="Vacio", hectares=2.0, crop_type="maiz")
        db.add(field)
        db.commit()

        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/predictions/accuracy")
        assert resp.status_code == 200
        body = resp.json()
        assert body["field_id"] == field.id
        assert body["field_name"] == "Vacio"
        assert body["total_predictions"] == 0
        assert body["resolved"] == 0
        assert body["pending"] == 0
        assert body["mape"] is None
        assert body["by_type"] == {}
        assert body["recent"] == []
        assert body["status"] == "green"

    def test_field_scoped_accuracy_excludes_other_fields(self, client, db):
        farm_a, field_a, farm_b, field_b = _seed_two_fields_with_predictions(db)

        resp = client.get(f"/api/farms/{farm_a.id}/fields/{field_a.id}/predictions/accuracy")
        assert resp.status_code == 200
        body = resp.json()

        assert body["field_id"] == field_a.id
        assert body["field_name"] == "Parcela A1"
        # 3 yield (2 resolved, 1 pending) + 1 health resolved = 4 total
        assert body["total_predictions"] == 4
        assert body["resolved"] == 3
        assert body["pending"] == 1

        # MAPE should be far below 400% — field_b's bad prediction must be excluded
        assert body["mape"] is not None
        assert body["mape"] < 15.0

        assert "yield" in body["by_type"]
        assert "health" in body["by_type"]
        assert body["by_type"]["yield"]["total"] == 3
        assert body["by_type"]["yield"]["resolved"] == 2
        assert body["by_type"]["yield"]["pending"] == 1
        assert body["by_type"]["health"]["total"] == 1
        assert body["by_type"]["health"]["resolved"] == 1

    def test_known_mape_calculation(self, client, db):
        """Exact MAPE check: two predictions with deterministic errors."""
        farm = Farm(name="Exact", state="Jalisco", total_hectares=10.0)
        db.add(farm)
        db.flush()
        field = Field(farm_id=farm.id, name="Exacta", hectares=5.0, crop_type="maiz")
        db.add(field)
        db.flush()

        now = datetime.utcnow()
        # APE 10% and 20% -> mean 15.0
        db.add(PredictionSnapshot(
            field_id=field.id, prediction_type="yield",
            predicted_value=110.0, actual_value=100.0,
            predicted_at=now - timedelta(days=30), resolved_at=now - timedelta(days=1),
        ))
        db.add(PredictionSnapshot(
            field_id=field.id, prediction_type="yield",
            predicted_value=120.0, actual_value=100.0,
            predicted_at=now - timedelta(days=20), resolved_at=now - timedelta(days=1),
        ))
        db.commit()

        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/predictions/accuracy")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_predictions"] == 2
        assert body["resolved"] == 2
        assert body["pending"] == 0
        assert body["mape"] == 15.0
        assert body["status"] == "green"

    def test_recent_list_includes_error_pct(self, client, db):
        farm_a, field_a, farm_b, field_b = _seed_two_fields_with_predictions(db)
        resp = client.get(f"/api/farms/{farm_a.id}/fields/{field_a.id}/predictions/accuracy")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["recent"]) == 4
        # Pending prediction has no error_pct
        pending = [r for r in body["recent"] if r["actual_value"] is None]
        assert len(pending) == 1
        assert pending[0]["error_pct"] is None
        # Resolved ones have error_pct
        resolved = [r for r in body["recent"] if r["actual_value"] is not None]
        assert all(r["error_pct"] is not None for r in resolved)
