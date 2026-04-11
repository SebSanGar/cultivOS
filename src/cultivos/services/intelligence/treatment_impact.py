"""Service: farm treatment impact summary.

For a given farm, groups TreatmentRecord entries (from its fields) within the
specified time window by (crop_type, problema). Computes avg_health_delta using
the first HealthScore within 30 days after each treatment. Only treatments with
at least one followup score are counted.
"""

from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord
from cultivos.models.treatment_impact import TreatmentImpactItem, TreatmentImpactOut


def _interpretation_es(avg_delta: float) -> str:
    """Return a Spanish sentence describing the treatment effectiveness."""
    if avg_delta >= 15:
        return f"Mejora significativa: promedio de +{avg_delta:.1f} puntos de salud tras el tratamiento."
    if avg_delta >= 5:
        return f"Mejora moderada: promedio de +{avg_delta:.1f} puntos de salud tras el tratamiento."
    if avg_delta >= 0:
        return f"Mejora leve o sin cambio: promedio de +{avg_delta:.1f} puntos."
    return f"Sin mejora detectada: promedio de {avg_delta:.1f} puntos tras el tratamiento."


def compute_treatment_impact(
    farm: Farm,
    db: Session,
    days: int = 90,
) -> TreatmentImpactOut:
    """Return per-(crop_type, problema) treatment effectiveness for a farm.

    Only treatments within the last `days` days are considered.
    Only treatments with a HealthScore within 30 days of created_at are counted.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)

    # Get all field IDs for this farm
    field_ids = [f.id for f in db.query(Field.id).filter(Field.farm_id == farm.id).all()]

    if not field_ids:
        return TreatmentImpactOut(farm_id=farm.id, period_days=days, treatments=[])

    # Fetch treatments in window for this farm's fields
    treatments = (
        db.query(TreatmentRecord, Field.crop_type)
        .join(Field, TreatmentRecord.field_id == Field.id)
        .filter(
            TreatmentRecord.field_id.in_(field_ids),
            TreatmentRecord.created_at >= cutoff,
        )
        .all()
    )

    # Group: (crop_type, problema) → health deltas
    groups: dict[tuple, list[float]] = defaultdict(list)
    counts: dict[tuple, int] = defaultdict(int)

    for treatment, crop_type in treatments:
        key = (crop_type or "unknown", treatment.problema)
        counts[key] += 1

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

    items = []
    for key, deltas in groups.items():
        if not deltas:
            continue
        crop_type, problema = key
        avg_delta = round(sum(deltas) / len(deltas), 2)
        items.append(TreatmentImpactItem(
            crop_type=crop_type,
            problema=problema,
            count=counts[key],
            avg_health_delta=avg_delta,
            interpretation_es=_interpretation_es(avg_delta),
        ))

    items.sort(key=lambda x: x.avg_health_delta, reverse=True)

    return TreatmentImpactOut(farm_id=farm.id, period_days=days, treatments=items)
