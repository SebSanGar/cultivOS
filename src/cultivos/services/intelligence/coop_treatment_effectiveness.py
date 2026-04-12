"""Service: cooperative-level treatment effectiveness aggregate.

Aggregates TreatmentRecord outcomes across all member farms of a cooperative,
grouped by (crop_type, problema). Follows the same 30-day HealthScore window
as compute_treatment_outcomes but adds participating_farms_count.
"""

from collections import defaultdict
from datetime import timedelta

from sqlalchemy.orm import Session

from cultivos.db.models import Cooperative, Farm, Field, HealthScore, TreatmentRecord


def compute_coop_treatment_effectiveness(coop: Cooperative, db: Session) -> dict:
    treatments = (
        db.query(TreatmentRecord, Field.crop_type, Farm.id)
        .join(Field, TreatmentRecord.field_id == Field.id)
        .join(Farm, Field.farm_id == Farm.id)
        .filter(Farm.cooperative_id == coop.id)
        .all()
    )

    deltas: dict[tuple, list[float]] = defaultdict(list)
    usage: dict[tuple, int] = defaultdict(int)
    farms_per_group: dict[tuple, set] = defaultdict(set)

    for treatment, crop_type, farm_id in treatments:
        key = (crop_type or "unknown", treatment.problema)
        usage[key] += 1

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
            deltas[key].append(followup.score - treatment.health_score_used)
            farms_per_group[key].add(farm_id)

    groups = []
    for key, vals in deltas.items():
        if not vals:
            continue
        crop, problema = key
        groups.append({
            "crop_type": crop,
            "treatment_summary": problema,
            "avg_health_delta": round(sum(vals) / len(vals), 2),
            "usage_count": usage[key],
            "participating_farms_count": len(farms_per_group[key]),
        })

    groups.sort(key=lambda g: g["avg_health_delta"], reverse=True)
    return {"cooperative_id": coop.id, "groups": groups}
