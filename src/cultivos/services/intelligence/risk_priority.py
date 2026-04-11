"""Risk-weighted field priority list service.

GET /api/farms/{farm_id}/risk-priority

For each field in the farm:
  stress_score        = compute_stress_composite(field, db).stress_index
  days_since_treatment = days since latest TreatmentRecord.created_at (capped at 90; 90 if none)
  priority_score      = stress_score * min(days, 90) / 90

Results sorted by priority_score DESC.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, TreatmentRecord
from cultivos.services.intelligence.stress_composite import compute_stress_composite

_MAX_DAYS = 90


def compute_risk_priority(farm: Farm, db: Session) -> list[dict]:
    """Return fields ranked by risk-weighted priority score."""
    fields = db.query(Field).filter(Field.farm_id == farm.id).all()

    if not fields:
        return []

    field_ids = [f.id for f in fields]

    # Latest treatment date per field
    latest_treatments = (
        db.query(TreatmentRecord.field_id, func.max(TreatmentRecord.created_at).label("last_tx"))
        .filter(TreatmentRecord.field_id.in_(field_ids))
        .group_by(TreatmentRecord.field_id)
        .all()
    )
    last_tx_by_field = {row.field_id: row.last_tx for row in latest_treatments}

    now = datetime.utcnow()
    results = []

    for field in fields:
        # Stress score
        composite = compute_stress_composite(field, db)
        stress_score = composite["stress_index"]
        recommendation_es = composite["recommendation_es"]

        # Days since last treatment (capped at MAX_DAYS)
        last_tx = last_tx_by_field.get(field.id)
        if last_tx is not None:
            raw_days = (now - last_tx).days
            days_since_treatment = min(raw_days, _MAX_DAYS)
        else:
            days_since_treatment = _MAX_DAYS

        priority_score = round(stress_score * days_since_treatment / _MAX_DAYS, 2)

        results.append({
            "field_id": field.id,
            "crop_type": field.crop_type,
            "stress_score": stress_score,
            "days_since_treatment": days_since_treatment,
            "priority_score": priority_score,
            "recommendation_es": recommendation_es,
        })

    results.sort(key=lambda x: x["priority_score"], reverse=True)
    return results
