"""Fertilizer recommendation for field stress service.

POST /api/intel/fertilizer-for-stress body: {farm_id, field_id}

Logic:
1. Compute stress composite for the field.
2. If stress_level in ("none", "low") → return {message_es} (no urgency).
3. Otherwise:
   - Query Fertilizer where suitable_crops=[] (universal) OR crop_type in suitable_crops.
   - Sort by cost_per_ha_mxn ASC, take top 3.
   - Build why_now_es from stress_level + dominant stress component.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from cultivos.db.models import Fertilizer
from cultivos.db.models import Field
from cultivos.services.intelligence.stress_composite import compute_stress_composite

_NO_URGENCY_LEVELS = {"none", "low"}

_WHY_NOW: dict[str, str] = {
    "moderate": "El campo presenta estrés moderado — aplicar fertilizante ayuda a fortalecer la planta.",
    "high": "El campo tiene estrés alto — el fertilizante mejora la resiliencia de la planta ante condiciones difíciles.",
    "critical": "Estrés crítico detectado — el fertilizante orgánico es urgente para mantener el cultivo.",
}


def compute_fertilizer_for_stress(field: Field, db: Session) -> dict:
    """Return fertilizer recommendations based on current field stress level."""
    composite = compute_stress_composite(field, db)
    stress_level = composite["stress_level"]

    if stress_level in _NO_URGENCY_LEVELS:
        return {
            "message_es": (
                "Sin urgencia de fertilización — el campo no presenta estrés significativo. "
                "Mantener el plan de nutrición habitual."
            )
        }

    # Filter fertilizers: universal (empty suitable_crops) or matching crop type
    all_fertilizers = db.query(Fertilizer).order_by(Fertilizer.cost_per_ha_mxn.asc()).all()
    matching = [
        f for f in all_fertilizers
        if not f.suitable_crops or field.crop_type in f.suitable_crops
    ]
    top3 = matching[:3]

    why_now_es = _WHY_NOW.get(stress_level, "Se recomienda aplicar fertilizante orgánico.")

    recommendations = [
        {
            "fertilizer_name": f.name,
            "why_now_es": why_now_es,
            "application_es": f.application_method,
        }
        for f in top3
    ]

    return {
        "field_id": field.id,
        "crop_type": field.crop_type,
        "stress_level": stress_level,
        "recommendations": recommendations,
    }
