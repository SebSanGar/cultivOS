"""Field crop stress composite index service.

Combines three sensor signals into one composite stress score (0-100):
  water_stress  (40%) — from urgency_level of compute_water_stress
  disease_risk  (35%) — risk_score from compute_disease_risk_assessment
  thermal_stress (25%) — latest ThermalResult.stress_pct

urgency_level → numeric:
  none     → 0
  low      → 25
  moderate → 50
  severe   → 100

Missing data → neutral 50 for that component.

stress_level thresholds:
  none     < 20
  low      20-39
  moderate 40-59
  high     60-79
  critical ≥ 80
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from cultivos.db.models import Field, ThermalResult
from cultivos.services.intelligence.disease_risk_assessment import (
    compute_disease_risk_assessment,
)
from cultivos.services.intelligence.water_stress import compute_water_stress

_URGENCY_TO_SCORE = {
    "none": 0.0,
    "low": 25.0,
    "moderate": 50.0,
    "severe": 100.0,
}

_NEUTRAL = 50.0


def _water_component(field: Field, db: Session) -> float:
    try:
        result = compute_water_stress(field, db)
        urgency = result.get("urgency_level", "none")
        return _URGENCY_TO_SCORE.get(urgency, _NEUTRAL)
    except Exception:
        return _NEUTRAL


def _disease_component(field: Field, db: Session) -> float:
    try:
        result = compute_disease_risk_assessment(field, db)
        return float(result.get("risk_score", _NEUTRAL))
    except Exception:
        return _NEUTRAL


def _thermal_component(field: Field, db: Session) -> float:
    record = (
        db.query(ThermalResult)
        .filter(ThermalResult.field_id == field.id)
        .order_by(ThermalResult.analyzed_at.desc())
        .first()
    )
    if record is None:
        return _NEUTRAL
    return float(record.stress_pct)


def _stress_level(index: float) -> str:
    if index < 20:
        return "none"
    if index < 40:
        return "low"
    if index < 60:
        return "moderate"
    if index < 80:
        return "high"
    return "critical"


_RECOMMENDATIONS = {
    "none": "Campo en condiciones optimas. Mantener monitoreo rutinario.",
    "low": "Estres leve detectado. Revisar humedad del suelo y condiciones climaticas.",
    "moderate": "Estres moderado. Considerar riego preventivo y revision de plagas.",
    "high": "Estres alto. Aplicar medidas correctivas: riego, tratamiento organico urgente.",
    "critical": "Estres critico. Intervencion inmediata requerida en campo.",
}


def compute_stress_composite(field: Field, db: Session) -> dict:
    """Return composite stress index for the field."""
    water = _water_component(field, db)
    disease = _disease_component(field, db)
    thermal = _thermal_component(field, db)

    stress_index = round(water * 0.40 + disease * 0.35 + thermal * 0.25, 1)
    level = _stress_level(stress_index)

    return {
        "field_id": field.id,
        "stress_index": stress_index,
        "stress_level": level,
        "components": {
            "water": round(water, 1),
            "disease": round(disease, 1),
            "thermal": round(thermal, 1),
        },
        "recommendation_es": _RECOMMENDATIONS[level],
    }
