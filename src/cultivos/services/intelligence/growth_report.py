"""Crop growth health report service.

Compares a field's current health against the expected health for its
phenological growth stage to determine if the crop is on track.

Logic:
  expected_stage = compute_growth_stage(crop_type, planted_at).stage
  health_vs_expected = latest_health_score / expected_health_for_stage
  on_track = health_vs_expected >= 0.9  (delta < 0.1 from expected)
  lag_days = round((1 - ratio) * stage_duration) when behind, else 0

Graceful degradation:
  - No planted_at  → stage fields None, on_track None, lag_days 0
  - No HealthScore → health_vs_expected None, on_track None
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from cultivos.db.models import Field, HealthScore
from cultivos.services.crop.phenology import compute_growth_stage


# Expected health score (0-100) per phenological stage
_EXPECTED_HEALTH: dict[str, float] = {
    "siembra":        65.0,
    "vegetativo":     72.0,
    "floracion":      78.0,
    "fructificacion": 73.0,
    "cosecha":        65.0,
}
_DEFAULT_EXPECTED_HEALTH = 70.0

# Approximate duration of each stage in days (generic — used for lag estimation)
_STAGE_DURATION: dict[str, int] = {
    "siembra":        15,
    "vegetativo":     40,
    "floracion":      25,
    "fructificacion": 40,
    "cosecha":        30,
}
_DEFAULT_STAGE_DURATION = 30

# On-track threshold: ratio must be >= this to be considered on track
_ON_TRACK_THRESHOLD = 0.9

# Severely lagging threshold: ratio < this triggers organic fertilizer recommendation
_SEVERE_LAG_THRESHOLD = 0.7


def compute_growth_report(field: Field, db: Session) -> dict:
    """Build a crop growth health report for a single field.

    Returns a dict with keys:
        field_id, crop_type, current_stage, expected_stage, on_track,
        health_vs_expected, lag_days, recommendations
    """
    # --- Phenology stage from planting date ---
    stage_result = compute_growth_stage(
        crop_type=field.crop_type or "",
        planted_at=field.planted_at,
        reference_date=datetime.utcnow(),
    )

    if stage_result is None:
        # No planting date → cannot compute stage
        return {
            "field_id": field.id,
            "crop_type": field.crop_type,
            "current_stage": None,
            "expected_stage": None,
            "on_track": None,
            "health_vs_expected": None,
            "lag_days": 0,
            "recommendations": [
                "Sin fecha de siembra registrada — ingrese la fecha de plantación para activar el seguimiento de etapas."
            ],
        }

    stage_name = stage_result["stage"]
    expected_health = _EXPECTED_HEALTH.get(stage_name, _DEFAULT_EXPECTED_HEALTH)
    stage_duration = _STAGE_DURATION.get(stage_name, _DEFAULT_STAGE_DURATION)

    # --- Latest health score ---
    health = (
        db.query(HealthScore)
        .filter(HealthScore.field_id == field.id)
        .order_by(HealthScore.scored_at.desc())
        .first()
    )

    if health is None:
        return {
            "field_id": field.id,
            "crop_type": field.crop_type,
            "current_stage": stage_name,
            "expected_stage": stage_name,
            "on_track": None,
            "health_vs_expected": None,
            "lag_days": 0,
            "recommendations": [
                "Sin datos de salud disponibles — realizar evaluación de campo."
            ],
        }

    # --- Compute ratio and lag ---
    ratio = health.score / expected_health
    on_track = ratio >= _ON_TRACK_THRESHOLD

    if on_track:
        lag_days = 0
    else:
        lag_days = max(0, round((1.0 - ratio) * stage_duration))

    # --- Recommendations ---
    recommendations: list[str] = []

    if on_track:
        recommendations.append(
            f"El cultivo avanza conforme al calendario esperado ({stage_name})."
        )
    else:
        if ratio < _SEVERE_LAG_THRESHOLD:
            recommendations.append(
                "Aplicar abono orgánico para recuperar vigor — el cultivo está significativamente por debajo del umbral esperado."
            )
        if lag_days > 14:
            recommendations.append(
                "Verificar riego — posible déficit hídrico que retrasa el desarrollo."
            )
        if ratio >= _SEVERE_LAG_THRESHOLD:
            recommendations.append(
                "Monitorear de cerca — ligero atraso detectado. Revisar nutrición y riego."
            )

    return {
        "field_id": field.id,
        "crop_type": field.crop_type,
        "current_stage": stage_name,
        "expected_stage": stage_name,
        "on_track": on_track,
        "health_vs_expected": round(ratio, 4),
        "lag_days": lag_days,
        "recommendations": recommendations,
    }
