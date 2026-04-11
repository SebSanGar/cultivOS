"""Service: per-crop treatment effectiveness summary.

For each (crop_type, problema) pair, compute avg_health_delta from treatments
that have a HealthScore recorded within 30 days of the treatment's created_at.
"""

from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional

from sqlalchemy.orm import Session

from cultivos.db.models import Field, HealthScore, TreatmentRecord


def compute_treatment_outcomes(
    db: Session,
    crop_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> list[dict]:
    """Return per-(crop_type, problema) effectiveness stats.

    Only treatments with at least one HealthScore within 30 days are included.
    avg_health_delta = avg(first_score_within_30d - health_score_used).
    """
    # Query all treatments with their field's crop_type
    query = (
        db.query(TreatmentRecord, Field.crop_type)
        .join(Field, TreatmentRecord.field_id == Field.id)
    )
    if crop_type:
        query = query.filter(Field.crop_type == crop_type)
    if start_date:
        query = query.filter(TreatmentRecord.created_at >= start_date)
    if end_date:
        query = query.filter(TreatmentRecord.created_at <= end_date)

    treatments = query.all()

    # Group: (crop_type, problema) → list of health_deltas
    groups: dict[tuple, list[float]] = defaultdict(list)
    usage_counts: dict[tuple, int] = defaultdict(int)

    for treatment, field_crop_type in treatments:
        key = (field_crop_type or "unknown", treatment.problema)
        usage_counts[key] += 1

        # Find first HealthScore within 30 days after treatment created_at
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
            delta = followup.score - treatment.health_score_used
            groups[key].append(delta)

    # Build result: only keys that have at least one followup
    results = []
    for key, deltas in groups.items():
        if not deltas:
            continue
        crop, problema = key
        avg_delta = sum(deltas) / len(deltas)
        results.append({
            "crop_type": crop,
            "treatment_summary": problema,
            "avg_health_delta": round(avg_delta, 2),
            "usage_count": usage_counts[key],
        })

    results.sort(key=lambda x: x["avg_health_delta"], reverse=True)
    return results
