"""Cooperative FODECIJAL readiness score service.

Aggregates 5 sub-scores across all member farms:
  1. data_completeness (weight 0.20) — from compute_data_completeness per farm
  2. regen_score      (weight 0.20) — from compute_regen_adoption
  3. tek_alignment    (weight 0.25) — from compute_tek_alignment per field
  4. sensor_freshness (weight 0.15) — from compute_sensor_freshness per farm
  5. treatment_effectiveness (weight 0.20) — from compute_treatment_impact per farm

overall_score = weighted avg of sub-scores (0-100).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from cultivos.db.models import Cooperative, Farm, Field
from cultivos.models.fodecijal_readiness import FodecijalReadinessOut, FodecijalSubScore
from cultivos.services.intelligence.completeness import compute_data_completeness
from cultivos.services.intelligence.regen_adoption import compute_regen_adoption
from cultivos.services.intelligence.sensor_freshness import compute_sensor_freshness
from cultivos.services.intelligence.tek_alignment import compute_tek_alignment
from cultivos.services.intelligence.treatment_impact import compute_treatment_impact

# Weights — must sum to 1.0
_WEIGHTS = {
    "data_completeness": 0.20,
    "regen_score": 0.20,
    "tek_alignment": 0.25,
    "sensor_freshness": 0.15,
    "treatment_effectiveness": 0.20,
}

_SENSOR_COUNT = 4  # ndvi, soil, health, weather
_STALE_DAYS = 14


def _avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 2) if values else 0.0


def _compute_data_completeness_avg(farms: list[Farm], db: Session) -> tuple[float, str]:
    """Average farm_score across all farms. Returns (score, evidence_es)."""
    scores = []
    for farm in farms:
        try:
            result = compute_data_completeness(db, farm.id)
            scores.append(result["farm_score"])
        except (ValueError, KeyError):
            scores.append(0.0)

    avg = _avg(scores)
    if not farms:
        return 0.0, "Sin granjas en la cooperativa."
    return avg, f"Completitud promedio de datos: {avg:.0f}% en {len(farms)} granja(s)."


def _compute_regen_score_avg(coop: Cooperative, db: Session) -> tuple[float, str]:
    """Overall regen score from regen adoption. Returns (score, evidence_es)."""
    result = compute_regen_adoption(coop, 90, db)
    score = result["overall_regen_score_avg"]
    farm_count = len(result["farms"])
    if farm_count == 0:
        return 0.0, "Sin granjas para evaluar adopción regenerativa."
    return round(score, 2), (
        f"Puntaje regenerativo promedio: {score:.0f}/100 en {farm_count} granja(s)."
    )


def _compute_tek_alignment_avg(farms: list[Farm], db: Session) -> tuple[float, str]:
    """Average TEK alignment across all fields. Returns (score, evidence_es)."""
    current_month = datetime.utcnow().month
    alignment_scores = []

    for farm in farms:
        fields = db.query(Field).filter(Field.farm_id == farm.id).all()
        for field in fields:
            try:
                result = compute_tek_alignment(field, current_month, db)
                alignment_scores.append(result["alignment_score_pct"])
            except Exception:
                alignment_scores.append(0.0)

    avg = _avg(alignment_scores)
    if not alignment_scores:
        return 0.0, "Sin parcelas para evaluar alineación TEK."
    return avg, (
        f"Alineación TEK-sensor promedio: {avg:.0f}% en "
        f"{len(alignment_scores)} parcela(s)."
    )


def _compute_sensor_freshness_score(farms: list[Farm], db: Session) -> tuple[float, str]:
    """Freshness score: % of non-stale sensors across all fields. Returns (score, evidence_es)."""
    total_sensors = 0
    fresh_sensors = 0

    for farm in farms:
        result = compute_sensor_freshness(farm, db)
        for field_item in result["fields"]:
            stale_count = len(field_item["stale_sensors"])
            total_sensors += _SENSOR_COUNT
            fresh_sensors += (_SENSOR_COUNT - stale_count)

    if total_sensors == 0:
        if not farms:
            return 0.0, "Sin granjas para evaluar sensores."
        return 0.0, "Sin parcelas con datos de sensores."

    score = round((fresh_sensors / total_sensors) * 100, 2)
    return score, (
        f"Frescura de sensores: {fresh_sensors}/{total_sensors} sensores actualizados "
        f"({score:.0f}%)."
    )


def _compute_treatment_effectiveness_avg(
    farms: list[Farm], db: Session,
) -> tuple[float, str]:
    """Avg health delta from treatments, normalized to 0-100. Returns (score, evidence_es)."""
    all_deltas = []

    for farm in farms:
        result = compute_treatment_impact(farm, db, days=90)
        for item in result.treatments:
            if item.avg_health_delta is not None:
                all_deltas.append(item.avg_health_delta)

    if not all_deltas:
        if not farms:
            return 0.0, "Sin granjas para evaluar tratamientos."
        return 0.0, "Sin tratamientos con seguimiento de efectividad."

    avg_delta = sum(all_deltas) / len(all_deltas)
    # Normalize: health delta of +20 → 100, 0 → 0, negative → 0
    score = round(max(0.0, min(100.0, (avg_delta / 20.0) * 100.0)), 2)
    return score, (
        f"Efectividad promedio de tratamientos: {avg_delta:+.1f} puntos de salud "
        f"({len(all_deltas)} tratamiento(s) evaluados)."
    )


def compute_fodecijal_readiness(coop: Cooperative, db: Session) -> FodecijalReadinessOut:
    """Compute FODECIJAL readiness composite score for a cooperative."""
    farms = db.query(Farm).filter(Farm.cooperative_id == coop.id).all()
    fields = []
    for farm in farms:
        fields.extend(db.query(Field).filter(Field.farm_id == farm.id).all())

    # Compute each sub-score
    completeness_score, completeness_ev = _compute_data_completeness_avg(farms, db)
    regen_score, regen_ev = _compute_regen_score_avg(coop, db)
    tek_score, tek_ev = _compute_tek_alignment_avg(farms, db)
    freshness_score, freshness_ev = _compute_sensor_freshness_score(farms, db)
    treatment_score, treatment_ev = _compute_treatment_effectiveness_avg(farms, db)

    sub_scores = [
        FodecijalSubScore(
            name="data_completeness",
            score=completeness_score,
            weight=_WEIGHTS["data_completeness"],
            evidence_es=completeness_ev,
        ),
        FodecijalSubScore(
            name="regen_score",
            score=regen_score,
            weight=_WEIGHTS["regen_score"],
            evidence_es=regen_ev,
        ),
        FodecijalSubScore(
            name="tek_alignment",
            score=tek_score,
            weight=_WEIGHTS["tek_alignment"],
            evidence_es=tek_ev,
        ),
        FodecijalSubScore(
            name="sensor_freshness",
            score=freshness_score,
            weight=_WEIGHTS["sensor_freshness"],
            evidence_es=freshness_ev,
        ),
        FodecijalSubScore(
            name="treatment_effectiveness",
            score=treatment_score,
            weight=_WEIGHTS["treatment_effectiveness"],
            evidence_es=treatment_ev,
        ),
    ]

    overall = round(sum(s.score * s.weight for s in sub_scores), 2)

    return FodecijalReadinessOut(
        cooperative_id=coop.id,
        overall_score=overall,
        sub_scores=sub_scores,
        farm_count=len(farms),
        field_count=len(fields),
    )
