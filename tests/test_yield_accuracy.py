"""Tests for GET /api/farms/{farm_id}/yield-accuracy endpoint.

Accuracy formula: per prediction = max(0, 100 - abs(predicted - actual) / actual * 100)
Grades: green >= 70%, yellow 60-69.9%, red < 60%
"""

import pytest
from datetime import datetime
from cultivos.db.models import Farm, Field, PredictionSnapshot


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_farm(db, name="Rancho Test"):
    farm = Farm(name=name, state="Jalisco", total_hectares=10.0)
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id, name="Campo Test", crop_type="maiz"):
    field = Field(farm_id=farm_id, name=name, crop_type=crop_type, hectares=5.0)
    db.add(field)
    db.commit()
    return field


def _add_prediction(db, field_id, predicted, actual, prediction_type="yield"):
    """Add a resolved PredictionSnapshot (actual_value set)."""
    ps = PredictionSnapshot(
        field_id=field_id,
        prediction_type=prediction_type,
        predicted_value=predicted,
        actual_value=actual,
        predicted_at=datetime.utcnow(),
        resolved_at=datetime.utcnow(),
    )
    db.add(ps)
    db.commit()
    return ps


def _add_open_prediction(db, field_id, predicted):
    """Add an unresolved PredictionSnapshot (actual_value is None) — should NOT be included."""
    ps = PredictionSnapshot(
        field_id=field_id,
        prediction_type="yield",
        predicted_value=predicted,
        actual_value=None,
        predicted_at=datetime.utcnow(),
    )
    db.add(ps)
    db.commit()
    return ps


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_404_unknown_farm(client, db):
    r = client.get("/api/farms/9999/yield-accuracy")
    assert r.status_code == 404


def test_response_schema_keys(client, db):
    """Response contains all required top-level keys."""
    farm = _make_farm(db)
    r = client.get(f"/api/farms/{farm.id}/yield-accuracy")
    assert r.status_code == 200
    data = r.json()
    for key in ("farm_id", "overall_accuracy_pct", "accuracy_grade", "fields"):
        assert key in data, f"Missing key: {key}"


def test_no_predictions_graceful(client, db):
    """Farm with no resolved predictions returns empty fields and None overall."""
    farm = _make_farm(db)
    _make_field(db, farm.id)

    r = client.get(f"/api/farms/{farm.id}/yield-accuracy")
    assert r.status_code == 200
    data = r.json()
    assert data["farm_id"] == farm.id
    assert data["overall_accuracy_pct"] is None
    assert data["fields"] == []


def test_open_predictions_excluded(client, db):
    """Unresolved (actual_value=None) predictions are not counted."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_open_prediction(db, field.id, 1000.0)

    r = client.get(f"/api/farms/{farm.id}/yield-accuracy")
    assert r.status_code == 200
    assert r.json()["overall_accuracy_pct"] is None
    assert r.json()["fields"] == []


def test_perfect_prediction_100_pct(client, db):
    """predicted == actual → 100% accuracy."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_prediction(db, field.id, predicted=1000.0, actual=1000.0)

    r = client.get(f"/api/farms/{farm.id}/yield-accuracy")
    assert r.status_code == 200
    data = r.json()
    assert data["overall_accuracy_pct"] == pytest.approx(100.0, abs=0.01)
    assert data["accuracy_grade"] == "green"
    assert data["fields"][0]["avg_accuracy_pct"] == pytest.approx(100.0, abs=0.01)
    assert data["fields"][0]["accuracy_grade"] == "green"


def test_accuracy_calculation_correct(client, db):
    """predicted=800, actual=1000 → accuracy = 100 - |800-1000|/1000 * 100 = 80%."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_prediction(db, field.id, predicted=800.0, actual=1000.0)

    r = client.get(f"/api/farms/{farm.id}/yield-accuracy")
    assert r.status_code == 200
    data = r.json()
    assert data["overall_accuracy_pct"] == pytest.approx(80.0, abs=0.01)
    assert data["accuracy_grade"] == "green"


def test_yellow_grade_threshold(client, db):
    """predicted=650, actual=1000 → accuracy = 100 - 35 = 65% → yellow grade."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_prediction(db, field.id, predicted=650.0, actual=1000.0)

    r = client.get(f"/api/farms/{farm.id}/yield-accuracy")
    assert r.status_code == 200
    data = r.json()
    assert data["overall_accuracy_pct"] == pytest.approx(65.0, abs=0.01)
    assert data["accuracy_grade"] == "yellow"


def test_red_grade_threshold(client, db):
    """predicted=200, actual=1000 → accuracy = 80% deviation → red grade."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_prediction(db, field.id, predicted=200.0, actual=1000.0)

    r = client.get(f"/api/farms/{farm.id}/yield-accuracy")
    assert r.status_code == 200
    data = r.json()
    # accuracy = max(0, 100 - 80) = 20% → red
    assert data["overall_accuracy_pct"] == pytest.approx(20.0, abs=0.01)
    assert data["accuracy_grade"] == "red"


def test_multiple_predictions_averaged(client, db):
    """Two predictions on same field: avg accuracy is their mean."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_prediction(db, field.id, predicted=900.0, actual=1000.0)  # 90% accurate
    _add_prediction(db, field.id, predicted=700.0, actual=1000.0)  # 70% accurate

    r = client.get(f"/api/farms/{farm.id}/yield-accuracy")
    assert r.status_code == 200
    data = r.json()
    assert data["fields"][0]["predictions_count"] == 2
    assert data["overall_accuracy_pct"] == pytest.approx(80.0, abs=0.01)  # (90+70)/2


def test_multi_field_overall_is_mean(client, db):
    """Farm with 2 fields: overall = mean of per-field accuracies."""
    farm = _make_farm(db)
    field1 = _make_field(db, farm.id, name="Campo A")
    field2 = _make_field(db, farm.id, name="Campo B")
    _add_prediction(db, field1.id, predicted=1000.0, actual=1000.0)  # 100%
    _add_prediction(db, field2.id, predicted=800.0, actual=1000.0)   # 80%

    r = client.get(f"/api/farms/{farm.id}/yield-accuracy")
    assert r.status_code == 200
    data = r.json()
    assert len(data["fields"]) == 2
    assert data["overall_accuracy_pct"] == pytest.approx(90.0, abs=0.01)  # (100+80)/2


def test_non_yield_predictions_excluded(client, db):
    """Health-type predictions are not included in yield accuracy."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_prediction(db, field.id, predicted=50.0, actual=100.0, prediction_type="health")

    r = client.get(f"/api/farms/{farm.id}/yield-accuracy")
    assert r.status_code == 200
    assert r.json()["fields"] == []


def test_field_item_schema_keys(client, db):
    """Each field item has all required keys."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id, crop_type="agave")
    _add_prediction(db, field.id, predicted=900.0, actual=1000.0)

    r = client.get(f"/api/farms/{farm.id}/yield-accuracy")
    assert r.status_code == 200
    item = r.json()["fields"][0]
    for key in ("field_id", "crop_type", "predictions_count", "avg_accuracy_pct", "accuracy_grade"):
        assert key in item, f"Missing key in field item: {key}"
    assert item["crop_type"] == "agave"
    assert item["field_id"] == field.id
