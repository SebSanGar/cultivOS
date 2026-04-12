"""Service: per-field intervention (treatment) effectiveness score (#206).

For each TreatmentRecord on a field within the window:
- baseline = HealthScore closest to applied_at within ±3 days
- followup = HealthScore closest to applied_at + 30d within ±3 days (27..33)
- delta = followup.score - baseline.score
- classify: effective (>=5), counterproductive (<=-5), else neutral

Aggregates per-treatment-name and returns best/worst by avg_delta.
Treatments missing baseline OR followup are skipped (not evaluated).
"""

from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from cultivos.db.models import Field, HealthScore, TreatmentRecord
from cultivos.models.field_intervention_effectiveness import (
    FieldInterventionEffectivenessOut,
    TreatmentEffectivenessRanked,
)


def _closest_score(
    db: Session, field_id: int, target: datetime, tolerance_days: int = 3
) -> HealthScore | None:
    lo = target - timedelta(days=tolerance_days)
    hi = target + timedelta(days=tolerance_days)
    rows = (
        db.query(HealthScore)
        .filter(
            HealthScore.field_id == field_id,
            HealthScore.scored_at >= lo,
            HealthScore.scored_at <= hi,
        )
        .all()
    )
    if not rows:
        return None
    return min(rows, key=lambda r: abs((r.scored_at - target).total_seconds()))


def _recommendation_es(evaluated: int, rate: float) -> str:
    if evaluated == 0:
        return "Sin tratamientos evaluables en el período. Registre fechas de aplicación y mediciones de salud para evaluar efectividad."
    if rate >= 70:
        return f"Excelente efectividad: {rate:.0f}% de los tratamientos mejoraron la salud del cultivo. Mantenga la estrategia actual."
    if rate >= 40:
        return f"Efectividad moderada: {rate:.0f}% de mejoras. Revise los tratamientos contraproducentes y favorezca los de mayor delta."
    return f"Baja efectividad: solo {rate:.0f}% de los tratamientos mejoraron la salud. Reconsidere el plan de intervenciones."


def compute_field_intervention_effectiveness(
    field: Field,
    db: Session,
    days: int = 180,
) -> FieldInterventionEffectivenessOut:
    cutoff = datetime.utcnow() - timedelta(days=days)

    treatments = (
        db.query(TreatmentRecord)
        .filter(
            TreatmentRecord.field_id == field.id,
            TreatmentRecord.applied_at.isnot(None),
            TreatmentRecord.applied_at >= cutoff,
        )
        .all()
    )

    deltas_by_name: dict[str, list[float]] = defaultdict(list)
    effective = neutral = counter = 0
    evaluated = 0

    for t in treatments:
        baseline = _closest_score(db, field.id, t.applied_at)
        followup = _closest_score(db, field.id, t.applied_at + timedelta(days=30))
        if baseline is None or followup is None:
            continue
        delta = followup.score - baseline.score
        deltas_by_name[t.tratamiento].append(delta)
        evaluated += 1
        if delta >= 5:
            effective += 1
        elif delta <= -5:
            counter += 1
        else:
            neutral += 1

    rate = round((effective / evaluated * 100), 1) if evaluated else 0.0

    best = worst = None
    if deltas_by_name:
        avgs = {
            name: round(sum(d) / len(d), 2) for name, d in deltas_by_name.items()
        }
        best_name = max(avgs, key=avgs.get)
        worst_name = min(avgs, key=avgs.get)
        best = TreatmentEffectivenessRanked(name=best_name, avg_delta=avgs[best_name])
        worst = TreatmentEffectivenessRanked(
            name=worst_name, avg_delta=avgs[worst_name]
        )

    return FieldInterventionEffectivenessOut(
        field_id=field.id,
        period_days=days,
        treatments_evaluated=evaluated,
        effective_count=effective,
        neutral_count=neutral,
        counterproductive_count=counter,
        effectiveness_rate_pct=rate,
        best_treatment=best,
        worst_treatment=worst,
        recommendation_es=_recommendation_es(evaluated, rate),
    )
