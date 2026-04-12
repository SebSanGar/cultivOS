"""Service: farm treatment ROI analysis (#203).

Groups TreatmentRecords by `tratamiento` text within a time window. Computes
cost_per_health_point = total_cost / total_positive_delta (None when no cost
or non-positive delta). Returns best (lowest positive cost/pt) and worst
(highest) treatment types, with a Spanish recommendation per row.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord
from cultivos.models.treatment_roi import TreatmentROIItem, TreatmentROIOut


def _recommendation_es(
    avg_delta: float,
    total_cost: int,
    cost_per_point: Optional[float],
) -> str:
    if avg_delta < 0:
        return f"Sin mejora medible (promedio {avg_delta:.1f} puntos) — no se recomienda repetir."
    if total_cost == 0:
        return "Sin datos de costo registrados — no se puede calcular ROI."
    if cost_per_point is None:
        return "Sin mejora medible — no se puede calcular ROI."
    if cost_per_point <= 50:
        return f"Excelente inversión: ${cost_per_point:.0f} MXN por punto de salud — repetir."
    if cost_per_point <= 150:
        return f"Buena inversión: ${cost_per_point:.0f} MXN por punto de salud."
    return (
        f"Inversión cuestionable: ${cost_per_point:.0f} MXN por punto — "
        "evaluar alternativas más económicas."
    )


def compute_treatment_roi(
    farm: Farm,
    db: Session,
    days: int = 90,
) -> TreatmentROIOut:
    """Return per-treatment_type ROI for a farm over the last `days` days."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    field_ids = [f.id for f in db.query(Field.id).filter(Field.farm_id == farm.id).all()]
    if not field_ids:
        return TreatmentROIOut(
            farm_id=farm.id,
            period_days=days,
            treatments=[],
            best_roi_treatment=None,
            worst_roi_treatment=None,
        )

    treatments = (
        db.query(TreatmentRecord)
        .filter(
            TreatmentRecord.field_id.in_(field_ids),
            TreatmentRecord.created_at >= cutoff,
        )
        .all()
    )

    deltas: dict[str, list[float]] = defaultdict(list)
    costs: dict[str, int] = defaultdict(int)

    for treatment in treatments:
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
        if followup is None:
            continue
        key = treatment.tratamiento
        deltas[key].append(followup.score - treatment.health_score_used)
        costs[key] += int(treatment.costo_estimado_mxn or 0)

    items: list[TreatmentROIItem] = []
    for key, dlist in deltas.items():
        count = len(dlist)
        avg_delta = round(sum(dlist) / count, 2)
        total_cost = costs[key]
        sum_positive = sum(d for d in dlist if d > 0)
        cost_per_point: Optional[float]
        if total_cost == 0 or sum_positive <= 0 or avg_delta <= 0:
            cost_per_point = None
        else:
            cost_per_point = round(total_cost / sum_positive, 2)
        items.append(
            TreatmentROIItem(
                treatment_type=key,
                count=count,
                total_cost_mxn=total_cost,
                avg_health_delta=avg_delta,
                cost_per_health_point=cost_per_point,
                recommendation_es=_recommendation_es(avg_delta, total_cost, cost_per_point),
            )
        )

    # Sort: best (lowest positive cost/pt) first; rows with None ROI sink to the end.
    items.sort(
        key=lambda it: (
            it.cost_per_health_point is None,
            it.cost_per_health_point if it.cost_per_health_point is not None else 0.0,
        )
    )

    scored = [it for it in items if it.cost_per_health_point is not None]
    best = scored[0].treatment_type if scored else None
    worst = scored[-1].treatment_type if scored else None

    return TreatmentROIOut(
        farm_id=farm.id,
        period_days=days,
        treatments=items,
        best_roi_treatment=best,
        worst_roi_treatment=worst,
    )
