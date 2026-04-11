"""Field prioritization service — ranks farm fields by intervention urgency.

Reuses compute_field_stress_report() to produce a unified stress score per field,
then sorts fields from most to least critical and adds human-readable labels.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field
from cultivos.services.intelligence.stress_report import compute_field_stress_report


# Spanish-language action recommendations by stress level
_ACTION_BY_LEVEL: dict[str, str] = {
    "critical": "Intervención inmediata requerida — revisar el campo hoy.",
    "high":     "Acción correctiva en los próximos días — planificar tratamiento urgente.",
    "medium":   "Monitoreo activo — programar tratamiento esta semana.",
    "low":      "Mantener rutina de cuidado — sin acción urgente.",
}

# Human-readable source descriptions for top_issue labels
_SOURCE_LABEL: dict[str, str] = {
    "health":  "Salud general del cultivo baja",
    "thermal": "Estrés hídrico por temperatura detectado",
    "ndvi":    "Baja densidad vegetal (NDVI bajo)",
    "soil":    "pH del suelo fuera del rango óptimo",
}


def compute_field_priority(farm: Farm, db: Session) -> dict:
    """Rank all fields in a farm by urgency, highest stress first.

    Returns:
        {
          "farm_id": int,
          "fields": [
              {
                "field_id": int,
                "name": str,
                "crop_type": str | None,
                "priority_score": float,
                "top_issue": str,
                "recommended_action": str,
              },
              ...
          ]   # sorted by priority_score DESC
        }
    """
    fields: list[Field] = (
        db.query(Field).filter(Field.farm_id == farm.id).all()
    )

    ranked: list[dict] = []
    for field in fields:
        report = compute_field_stress_report(field, db)
        stress_score: float = report["stress_score"]
        stress_level: str = report["stress_level"]
        factors: list[dict] = report["contributing_factors"]

        # Derive top_issue: first contributing factor → label, or generic fallback
        if factors:
            top_source = factors[0]["source"]
            top_issue = _SOURCE_LABEL.get(top_source, f"Factor: {top_source}")
        else:
            top_issue = "Datos insuficientes — se usa estimación por defecto"

        recommended_action = _ACTION_BY_LEVEL.get(stress_level, _ACTION_BY_LEVEL["low"])

        ranked.append({
            "field_id": field.id,
            "name": field.name,
            "crop_type": field.crop_type,
            "priority_score": stress_score,
            "top_issue": top_issue,
            "recommended_action": recommended_action,
        })

    # Sort by priority_score descending (most urgent first)
    ranked.sort(key=lambda x: x["priority_score"], reverse=True)

    return {
        "farm_id": farm.id,
        "fields": ranked,
    }
