"""Yield prediction accuracy service — pure function, no HTTP, no side effects.

Aggregates resolved PredictionSnapshots (prediction_type='yield') for all fields
in a farm to compute per-field and farm-wide accuracy metrics.

Accuracy formula (per prediction):
    accuracy_pct = max(0, 100 - abs(predicted - actual) / actual * 100)

Grades:
    green  ≥ 70%
    yellow 60–69.9%
    red    < 60%
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, PredictionSnapshot
from cultivos.models.yield_accuracy import FieldYieldAccuracy, YieldAccuracyOut


def _accuracy_grade(pct: float) -> str:
    if pct >= 70.0:
        return "green"
    if pct >= 60.0:
        return "yellow"
    return "red"


def _field_accuracy(db: Session, field: Field) -> FieldYieldAccuracy | None:
    """Compute yield accuracy for a single field. Returns None if no resolved predictions."""
    snapshots = (
        db.query(PredictionSnapshot)
        .filter(
            PredictionSnapshot.field_id == field.id,
            PredictionSnapshot.prediction_type == "yield",
            PredictionSnapshot.actual_value.isnot(None),
        )
        .all()
    )
    if not snapshots:
        return None

    accuracies = []
    for ps in snapshots:
        if ps.actual_value and ps.actual_value != 0:
            acc = max(0.0, 100.0 - abs(ps.predicted_value - ps.actual_value) / ps.actual_value * 100.0)
        else:
            acc = 0.0
        accuracies.append(acc)

    avg = sum(accuracies) / len(accuracies)
    return FieldYieldAccuracy(
        field_id=field.id,
        crop_type=field.crop_type or "unknown",
        predictions_count=len(snapshots),
        avg_accuracy_pct=round(avg, 2),
        accuracy_grade=_accuracy_grade(avg),
    )


def compute_yield_accuracy(db: Session, farm: Farm) -> YieldAccuracyOut:
    """Compute yield prediction accuracy for all fields in a farm."""
    fields = db.query(Field).filter(Field.farm_id == farm.id).all()

    field_results: list[FieldYieldAccuracy] = []
    for field in fields:
        result = _field_accuracy(db, field)
        if result is not None:
            field_results.append(result)

    if not field_results:
        return YieldAccuracyOut(
            farm_id=farm.id,
            overall_accuracy_pct=None,
            accuracy_grade=None,
            fields=[],
        )

    overall = sum(f.avg_accuracy_pct for f in field_results) / len(field_results)
    overall_rounded = round(overall, 2)

    return YieldAccuracyOut(
        farm_id=farm.id,
        overall_accuracy_pct=overall_rounded,
        accuracy_grade=_accuracy_grade(overall_rounded),
        fields=field_results,
    )
