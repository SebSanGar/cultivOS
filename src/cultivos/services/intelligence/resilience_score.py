"""Crop resilience score service.

Combines four sub-scores (each 0-100) with fixed weights:
  health_score        40%  — latest HealthScore.score
  soil_pH_optimal     20%  — how close pH is to the optimal 6.0–7.0 range
  water_stress_inv    20%  — inverse of water stress urgency
  disease_risk_inv    20%  — inverse of disease risk score

Missing component → 50 (neutral) so one absent sensor doesn't crash the score.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from cultivos.db.models import Field, HealthScore, SoilAnalysis
from cultivos.services.intelligence.water_stress import compute_water_stress
from cultivos.services.intelligence.disease_risk_assessment import compute_disease_risk_assessment

# Weights
_W_HEALTH = 0.40
_W_SOIL_PH = 0.20
_W_WATER = 0.20
_W_DISEASE = 0.20

_NEUTRAL = 50.0

# Water stress urgency → sub-score (0-100)
_WATER_SCORES: dict[str, float] = {
    "none": 100.0,
    "low": 75.0,
    "moderate": 50.0,
    "severe": 25.0,
}

_INTERPRETATIONS: list[tuple[float, str]] = [
    (80.0, "Campo resiliente — en buenas condiciones para resistir el estrés climático."),
    (60.0, "Resiliencia moderada — monitorear y aplicar insumos preventivos esta semana."),
    (40.0, "Resiliencia baja — campo vulnerable; priorizar intervención en los próximos 3 días."),
    (0.0, "Resiliencia crítica — acción urgente requerida para prevenir pérdida de cosecha."),
]


def _soil_ph_score(ph: float) -> float:
    """Convert soil pH to an optimality score (0-100).

    Optimal range 6.0–7.0 = 100. Outside degrades in steps.
    """
    if 6.0 <= ph <= 7.0:
        return 100.0
    if 5.5 <= ph < 6.0 or 7.0 < ph <= 7.5:
        return 75.0
    if 5.0 <= ph < 5.5 or 7.5 < ph <= 8.0:
        return 50.0
    return 25.0


def compute_resilience_score(field: Field, db: Session) -> dict:
    """Compute crop resilience score for a field.

    Returns a dict with keys:
        field_id, resilience_score, components, interpretation_es
    """
    # --- Health sub-score ---
    health_record = (
        db.query(HealthScore)
        .filter(HealthScore.field_id == field.id)
        .order_by(HealthScore.scored_at.desc())
        .first()
    )
    health_component: float | None = None
    if health_record is not None:
        health_component = float(health_record.score)

    # --- Soil pH sub-score ---
    soil = (
        db.query(SoilAnalysis)
        .filter(SoilAnalysis.field_id == field.id)
        .order_by(SoilAnalysis.created_at.desc())
        .first()
    )
    soil_ph_component: float | None = None
    if soil is not None and soil.ph is not None:
        soil_ph_component = _soil_ph_score(soil.ph)

    # --- Water stress inverse sub-score ---
    water_result = compute_water_stress(field, db)
    urgency = water_result.get("urgency_level", "none")
    water_component: float | None = _WATER_SCORES.get(urgency)

    # --- Disease risk inverse sub-score ---
    disease_result = compute_disease_risk_assessment(field, db)
    disease_risk_score = disease_result.get("risk_score", 0.0)
    disease_component: float | None = max(0.0, 100.0 - float(disease_risk_score))

    # --- Weighted sum with neutral fallback ---
    h = health_component if health_component is not None else _NEUTRAL
    s = soil_ph_component if soil_ph_component is not None else _NEUTRAL
    w = water_component if water_component is not None else _NEUTRAL
    d = disease_component if disease_component is not None else _NEUTRAL

    resilience = round(
        h * _W_HEALTH + s * _W_SOIL_PH + w * _W_WATER + d * _W_DISEASE,
        1,
    )
    resilience = max(0.0, min(100.0, resilience))

    # --- Interpretation ---
    interpretation_es = _INTERPRETATIONS[-1][1]
    for threshold, text in _INTERPRETATIONS:
        if resilience >= threshold:
            interpretation_es = text
            break

    return {
        "field_id": field.id,
        "resilience_score": resilience,
        "components": {
            "health": health_component,
            "soil_ph": soil_ph_component,
            "water_stress": water_component,
            "disease_risk": disease_component,
        },
        "interpretation_es": interpretation_es,
    }
