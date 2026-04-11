"""Field weekly action plan service.

Composes TEK calendar, upcoming treatments, and stress signals into a
prioritized weekly action list for the farmer.

Priority tiers:
  high   — severe/critical stress (thermal >= 70%, water=severe, disease >= 60)
  medium — moderate stress or urgent treatment window
  low    — TEK practices and scheduled maintenance

Categories: stress | treatment | tek
"""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from cultivos.db.models import AncestralMethod, Field, ThermalResult
from cultivos.services.intelligence.disease_risk_assessment import (
    compute_disease_risk_assessment,
)
from cultivos.services.intelligence.upcoming_treatments import compute_upcoming_treatments
from cultivos.services.intelligence.water_stress import compute_water_stress

_THERMAL_HIGH = 70.0
_THERMAL_MODERATE = 40.0
_DISEASE_HIGH = 60.0
_DISEASE_MODERATE = 30.0


def _latest_thermal_pct(field: Field, db: Session) -> float:
    record = (
        db.query(ThermalResult)
        .filter(ThermalResult.field_id == field.id)
        .order_by(ThermalResult.analyzed_at.desc())
        .first()
    )
    return float(record.stress_pct) if record else 0.0


def compose_action_plan(
    field: Field, days: int, db: Session
) -> dict:
    """Return dict matching ActionPlanOut schema."""
    actions: list[dict] = []

    # --- Stress signals ---
    try:
        water_result = compute_water_stress(field, db)
        water_urgency = water_result.get("urgency_level", "none")
    except Exception:
        water_urgency = "none"

    try:
        disease_result = compute_disease_risk_assessment(field, db)
        disease_score = float(disease_result.get("risk_score", 0.0))
    except Exception:
        disease_score = 0.0

    thermal_pct = _latest_thermal_pct(field, db)

    # Thermal stress action
    if thermal_pct >= _THERMAL_HIGH:
        actions.append({
            "priority": "high",
            "category": "stress",
            "action_es": (
                f"Estrés térmico severo ({thermal_pct:.0f}%). "
                "Aplicar riego inmediato o sombreado para proteger el cultivo."
            ),
            "source_es": "sensor_termico",
        })
    elif thermal_pct >= _THERMAL_MODERATE:
        actions.append({
            "priority": "medium",
            "category": "stress",
            "action_es": (
                f"Estrés térmico moderado ({thermal_pct:.0f}%). "
                "Monitorear temperatura y ajustar riego de ser necesario."
            ),
            "source_es": "sensor_termico",
        })

    # Water stress action
    if water_urgency == "severe":
        actions.append({
            "priority": "high",
            "category": "stress",
            "action_es": "Déficit hídrico severo. Riego urgente requerido en las próximas 24 horas.",
            "source_es": "sensor_hidrico",
        })
    elif water_urgency in ("moderate", "low"):
        actions.append({
            "priority": "medium",
            "category": "stress",
            "action_es": f"Estrés hídrico {water_urgency}. Revisar programación de riego esta semana.",
            "source_es": "sensor_hidrico",
        })

    # Disease risk action
    if disease_score >= _DISEASE_HIGH:
        actions.append({
            "priority": "high",
            "category": "stress",
            "action_es": (
                f"Riesgo de enfermedades alto ({disease_score:.0f}/100). "
                "Aplicar tratamiento orgánico preventivo de inmediato."
            ),
            "source_es": "sensor_enfermedad",
        })
    elif disease_score >= _DISEASE_MODERATE:
        actions.append({
            "priority": "medium",
            "category": "stress",
            "action_es": (
                f"Riesgo de enfermedades moderado ({disease_score:.0f}/100). "
                "Inspeccionar el cultivo y preparar tratamiento orgánico."
            ),
            "source_es": "sensor_enfermedad",
        })

    # --- Upcoming treatments ---
    try:
        treatments = compute_upcoming_treatments(field, db)
        for t in treatments[:2]:  # top 2 upcoming treatments
            actions.append({
                "priority": "medium",
                "category": "treatment",
                "action_es": f"{t.reason_es} (fecha: {t.recommended_date})",
                "source_es": "calendario_tratamientos",
            })
    except Exception:
        # Fallback generic treatment action
        actions.append({
            "priority": "low",
            "category": "treatment",
            "action_es": "Revisar calendario de tratamientos y aplicar próxima intervención programada.",
            "source_es": "calendario_tratamientos",
        })

    # --- TEK practices for current month ---
    crop_type = field.crop_type or ""
    current_month = date.today().month
    all_methods = db.query(AncestralMethod).all()
    applicable_tek = [
        m for m in all_methods
        if m.applicable_months and current_month in m.applicable_months
        and (not m.crops or crop_type.lower() in [c.lower() for c in m.crops])
    ]
    for method in applicable_tek:
        actions.append({
            "priority": "low",
            "category": "tek",
            "action_es": (
                f"{method.name}: {method.description_es or 'Práctica ancestral recomendada.'}"
            ),
            "source_es": f"conocimiento_ancestral:{method.name}",
        })

    return {
        "field_id": field.id,
        "crop_type": crop_type,
        "period_days": days,
        "actions": actions,
    }
