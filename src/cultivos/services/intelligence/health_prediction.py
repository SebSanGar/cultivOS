"""Field 30-day health prediction service.

GET /api/farms/{farm_id}/fields/{field_id}/health-prediction

Fits a linear trend on last 60 days of HealthScore records,
projects score at +30 days from now.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from cultivos.db.models import Field, HealthScore

_LOOKBACK_DAYS = 60
_PROJECTION_DAYS = 30
_SLOPE_THRESHOLD = 0.1  # per day — below this is "stable"


def _linear_regression(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Simple OLS: returns (slope, intercept). xs in days from earliest."""
    n = len(xs)
    if n < 2:
        return 0.0, ys[0] if ys else 0.0
    sum_x = sum(xs)
    sum_y = sum(ys)
    sum_xy = sum(x * y for x, y in zip(xs, ys))
    sum_xx = sum(x * x for x in xs)
    denom = n * sum_xx - sum_x * sum_x
    if denom == 0:
        return 0.0, sum_y / n
    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    return slope, intercept


def compute_health_prediction(field: Field, db: Session) -> dict:
    """Compute 30-day health prediction for a field."""
    now = datetime.utcnow()
    cutoff = now - timedelta(days=_LOOKBACK_DAYS)

    scores = (
        db.query(HealthScore)
        .filter(
            HealthScore.field_id == field.id,
            HealthScore.scored_at >= cutoff,
        )
        .order_by(HealthScore.scored_at.asc())
        .all()
    )

    n = len(scores)

    if n == 0:
        return {
            "field_id": field.id,
            "current_avg_health": 0.0,
            "predicted_health_30d": 0.0,
            "trend_direction": "stable",
            "confidence": "low",
            "risk_flag": False,
            "data_points": 0,
        }

    score_values = [s.score for s in scores]
    current_avg = round(sum(score_values) / n, 2)

    # Confidence tier
    if n >= 10:
        confidence = "high"
    elif n >= 5:
        confidence = "medium"
    else:
        confidence = "low"

    # Convert scored_at to days-from-earliest for regression
    earliest = scores[0].scored_at
    xs = [(s.scored_at - earliest).total_seconds() / 86400.0 for s in scores]
    ys = score_values

    slope, intercept = _linear_regression(xs, ys)

    # Project: days from earliest to now + 30
    days_to_projection = (now - earliest).total_seconds() / 86400.0 + _PROJECTION_DAYS
    predicted = slope * days_to_projection + intercept
    predicted = round(max(0.0, min(100.0, predicted)), 2)

    # Trend direction based on slope per day
    if slope > _SLOPE_THRESHOLD:
        trend = "improving"
    elif slope < -_SLOPE_THRESHOLD:
        trend = "declining"
    else:
        trend = "stable"

    risk_flag = predicted < 40

    return {
        "field_id": field.id,
        "current_avg_health": current_avg,
        "predicted_health_30d": predicted,
        "trend_direction": trend,
        "confidence": confidence,
        "risk_flag": risk_flag,
        "data_points": n,
    }
