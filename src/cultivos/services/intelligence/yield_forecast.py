"""Seasonal yield forecast service — pure function, no HTTP, no side effects.

Combines current health score + yield_model + PredictionSnapshot presence
to produce per-field yield forecasts for a farm.
"""

from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, HealthScore, PredictionSnapshot
from cultivos.models.yield_forecast import FarmYieldForecastOut, FieldYieldForecast
from cultivos.services.intelligence.yield_model import predict_yield, DEFAULT_BASELINE, UNCERTAINTY_BAND

# Fallback health score when no HealthScore records exist
FALLBACK_HEALTH_SCORE = 50.0


def _get_latest_health_score(db: Session, field_id: int) -> float | None:
    """Return the most recent health score for a field, or None if none exist."""
    hs = (
        db.query(HealthScore)
        .filter(HealthScore.field_id == field_id)
        .order_by(HealthScore.scored_at.desc())
        .first()
    )
    return hs.score if hs else None


def _has_yield_snapshot(db: Session, field_id: int) -> bool:
    """Return True if a yield-type PredictionSnapshot exists for this field."""
    return (
        db.query(PredictionSnapshot)
        .filter(
            PredictionSnapshot.field_id == field_id,
            PredictionSnapshot.prediction_type == "yield",
        )
        .first()
        is not None
    )


def _confidence(health_score: float | None, has_snapshot: bool) -> str:
    """Compute confidence tier based on data availability.

    - high: has a PredictionSnapshot AND recent health score >= 70
    - medium: has health score (any) but no snapshot
    - low: no health score (fallback estimate used)
    """
    if health_score is None:
        return "low"
    if has_snapshot and health_score >= 70:
        return "high"
    return "medium"


def compute_farm_yield_forecast(db: Session, farm: Farm) -> FarmYieldForecastOut:
    """Build yield forecast for all fields in a farm."""
    fields: list[Field] = (
        db.query(Field).filter(Field.farm_id == farm.id).all()
    )

    field_forecasts: list[FieldYieldForecast] = []
    for field in fields:
        health_score = _get_latest_health_score(db, field.id)
        has_snapshot = _has_yield_snapshot(db, field.id)

        score_for_calc = health_score if health_score is not None else FALLBACK_HEALTH_SCORE
        yield_result = predict_yield(
            crop_type=field.crop_type or "",
            hectares=field.hectares or 0.0,
            health_score=score_for_calc,
        )

        field_forecasts.append(
            FieldYieldForecast(
                field_id=field.id,
                field_name=field.name,
                crop_type=field.crop_type,
                projected_yield_kg=yield_result["total_kg"],
                confidence=_confidence(health_score, has_snapshot),
                health_score_used=health_score,
                has_prediction_snapshot=has_snapshot,
            )
        )

    return FarmYieldForecastOut(
        farm_id=farm.id,
        farm_name=farm.name,
        fields=field_forecasts,
    )
