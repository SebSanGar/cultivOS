"""TEK-sensor alignment service.

Matches AncestralMethod practices applicable to the requested month + field
crop_type against live sensor data (water stress, disease risk, thermal stress).

sensor_support rules by practice_type:
  water_management / water_retention → True if water urgency != "none"
  soil_management  / composting      → True if disease_score >= 25 OR thermal_pct >= 40
  intercropping                      → True if disease_score >= 25
  pest_control                       → True if disease_score >= 40
  default (any other type)           → True if any stress present

alignment_score_pct = (supported_count / total_count) * 100, or 0 when empty.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from cultivos.db.models import AncestralMethod, Field, ThermalResult
from cultivos.services.intelligence.disease_risk_assessment import compute_disease_risk_assessment
from cultivos.services.intelligence.water_stress import compute_water_stress

_NEUTRAL_THERMAL = 0.0  # when no ThermalResult, treat as no thermal stress


def _thermal_stress_pct(field: Field, db: Session) -> float:
    record = (
        db.query(ThermalResult)
        .filter(ThermalResult.field_id == field.id)
        .order_by(ThermalResult.analyzed_at.desc())
        .first()
    )
    return float(record.stress_pct) if record else _NEUTRAL_THERMAL


def _is_supported(
    practice_type: str,
    water_urgency: str,
    disease_score: float,
    thermal_pct: float,
) -> tuple[bool, str]:
    """Return (sensor_support, evidence_es) for a practice."""
    water_active = water_urgency != "none"
    disease_elevated = disease_score >= 25
    disease_high = disease_score >= 40
    thermal_stressed = thermal_pct >= 40
    any_stress = water_active or disease_elevated or thermal_stressed

    ptype = practice_type.lower()

    if ptype in ("water_management", "water_retention", "irrigation"):
        if water_active:
            return True, (
                f"Estrés hídrico detectado (nivel: {water_urgency}). "
                "Práctica de manejo de agua es prioritaria ahora."
            )
        return False, "No se detecta estrés hídrico. Práctica no urgente en este momento."

    if ptype in ("soil_management", "composting"):
        if disease_elevated:
            return True, (
                f"Riesgo de enfermedades elevado ({disease_score:.0f}/100). "
                "Enmienda de suelo mejora resistencia del cultivo."
            )
        if thermal_stressed:
            return True, (
                f"Estrés térmico elevado ({thermal_pct:.0f}%). "
                "Mejora de suelo ayuda a regular temperatura radicular."
            )
        return False, "Condiciones del suelo dentro de rangos normales."

    if ptype == "intercropping":
        if disease_elevated:
            return True, (
                f"Riesgo de enfermedades detectado ({disease_score:.0f}/100). "
                "El policultivo reduce la propagación de patógenos."
            )
        return False, "Sin riesgo elevado de enfermedades. Práctica preventiva recomendada."

    if ptype == "pest_control":
        if disease_high:
            return True, (
                f"Riesgo de plagas/enfermedades alto ({disease_score:.0f}/100). "
                "Aplicar método de control ancestral de inmediato."
            )
        return False, f"Riesgo de plagas moderado o bajo ({disease_score:.0f}/100)."

    # Default: support if any stress present
    if any_stress:
        return True, "Condiciones de estrés detectadas. Práctica tradicional recomendada."
    return False, "Sin estrés detectado. Monitoreo regular recomendado."


def compute_tek_alignment(field: Field, month: int, db: Session) -> dict:
    """Compute TEK-sensor alignment for a field in the given calendar month.

    Returns a dict matching TekAlignmentOut schema.
    """
    crop_type = field.crop_type or ""

    # --- Sensor signals ---
    try:
        water_result = compute_water_stress(field, db)
        water_urgency: str = water_result.get("urgency_level", "none")
    except Exception:
        water_urgency = "none"

    try:
        disease_result = compute_disease_risk_assessment(field, db)
        disease_score: float = float(disease_result.get("risk_score", 0.0))
        disease_level: str = disease_result.get("risk_level", "low")
    except Exception:
        disease_score = 0.0
        disease_level = "low"

    thermal_pct = _thermal_stress_pct(field, db)

    # --- TEK practices for this month and crop ---
    all_methods = db.query(AncestralMethod).all()
    applicable = [
        m for m in all_methods
        if m.applicable_months and month in m.applicable_months
        and (not m.crops or crop_type.lower() in [c.lower() for c in m.crops])
    ]

    practices: list[dict] = []
    supported_count = 0

    for method in applicable:
        support, evidence = _is_supported(
            method.practice_type or "general",
            water_urgency,
            disease_score,
            thermal_pct,
        )
        if support:
            supported_count += 1
        practices.append({
            "name": method.name,
            "timing_rationale": method.timing_rationale,
            "sensor_support": support,
            "evidence_es": evidence,
        })

    total = len(practices)
    alignment_score_pct = round((supported_count / total) * 100, 1) if total > 0 else 0.0

    return {
        "field_id": field.id,
        "month": month,
        "crop_type": crop_type,
        "alignment_score_pct": alignment_score_pct,
        "sensor_context": {
            "water_stress_level": water_urgency,
            "disease_risk_level": disease_level,
            "thermal_stress_pct": round(thermal_pct, 1),
        },
        "practices": practices,
    }
