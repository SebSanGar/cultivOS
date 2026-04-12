"""Service: organic treatment success rate by crop type.

Aggregates TreatmentRecord + 30-day HealthScore follow-up per (crop_type, problema).
success_rate_pct = percentage of treatments with strictly positive health delta.
"""

from datetime import timedelta
from collections import defaultdict
from typing import Optional

from sqlalchemy.orm import Session

from cultivos.db.models import Field, HealthScore, TreatmentRecord


def compute_treatment_success_rates(
    db: Session,
    crop_type: Optional[str] = None,
) -> list[dict]:
    query = (
        db.query(TreatmentRecord, Field.crop_type)
        .join(Field, TreatmentRecord.field_id == Field.id)
    )
    if crop_type:
        query = query.filter(Field.crop_type == crop_type)

    treatments = query.all()

    groups: dict[tuple, list[float]] = defaultdict(list)
    for treatment, field_crop_type in treatments:
        key = (field_crop_type or "unknown", treatment.problema)
        window_end = treatment.created_at + timedelta(days=30)
        followup = (
            db.query(HealthScore)
            .filter(
                HealthScore.field_id == treatment.field_id,
                HealthScore.scored_at > treatment.created_at,
                HealthScore.scored_at <= window_end,
            )
            .order_by(HealthScore.scored_at)
            .first()
        )
        if followup is not None:
            groups[key].append(followup.score - treatment.health_score_used)

    results = []
    for (crop, problema), deltas in groups.items():
        count = len(deltas)
        if count == 0:
            continue
        success_count = sum(1 for d in deltas if d > 0)
        results.append({
            "crop_type": crop,
            "problema": problema,
            "avg_health_delta": round(sum(deltas) / count, 2),
            "success_rate_pct": round((success_count / count) * 100, 2),
            "treatment_count": count,
        })

    results.sort(key=lambda x: x["success_rate_pct"], reverse=True)
    return results
