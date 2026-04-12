"""Annual farm performance summary service.

Per-field yearly aggregates: avg/min/max health, NDVI trend (last - first),
soil_ph_delta (last - first), treatments_applied, regen_score (% organic).
Farm-level rollup: best_field, most_improved_field, total_co2e_sequestered_t
(from carbon_audit), treatments_applied_total.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from cultivos.db.models import (
    Farm,
    Field,
    HealthScore,
    NDVIResult,
    SoilAnalysis,
    TreatmentRecord,
)
from cultivos.services.intelligence.carbon_audit import compute_carbon_audit


def _round(value: Optional[float], places: int = 2) -> Optional[float]:
    return round(value, places) if value is not None else None


def compute_annual_report(farm: Farm, year: int, db: Session) -> dict:
    year_start = datetime(year, 1, 1)
    year_end = datetime(year, 12, 31, 23, 59, 59)

    fields = db.query(Field).filter(Field.farm_id == farm.id).all()

    field_entries: list[dict] = []
    treatments_total = 0
    best_field_name: Optional[str] = None
    best_field_avg: Optional[float] = None
    most_improved_name: Optional[str] = None
    most_improved_delta: Optional[float] = None

    for field in fields:
        health_rows = (
            db.query(HealthScore.score, HealthScore.scored_at)
            .filter(
                HealthScore.field_id == field.id,
                HealthScore.scored_at >= year_start,
                HealthScore.scored_at <= year_end,
            )
            .order_by(HealthScore.scored_at.asc())
            .all()
        )
        if health_rows:
            scores = [r.score for r in health_rows]
            avg_h = sum(scores) / len(scores)
            min_h = min(scores)
            max_h = max(scores)
            health_delta = health_rows[-1].score - health_rows[0].score
        else:
            avg_h = min_h = max_h = None
            health_delta = None

        ndvi_rows = (
            db.query(NDVIResult.ndvi_mean, NDVIResult.analyzed_at)
            .filter(
                NDVIResult.field_id == field.id,
                NDVIResult.analyzed_at >= year_start,
                NDVIResult.analyzed_at <= year_end,
            )
            .order_by(NDVIResult.analyzed_at.asc())
            .all()
        )
        ndvi_trend: Optional[float] = None
        if len(ndvi_rows) >= 2:
            ndvi_trend = ndvi_rows[-1].ndvi_mean - ndvi_rows[0].ndvi_mean

        soil_rows = (
            db.query(SoilAnalysis.ph, SoilAnalysis.sampled_at)
            .filter(
                SoilAnalysis.field_id == field.id,
                SoilAnalysis.sampled_at >= year_start,
                SoilAnalysis.sampled_at <= year_end,
                SoilAnalysis.ph.isnot(None),
            )
            .order_by(SoilAnalysis.sampled_at.asc())
            .all()
        )
        soil_ph_delta: Optional[float] = None
        if len(soil_rows) >= 2:
            soil_ph_delta = soil_rows[-1].ph - soil_rows[0].ph

        treatment_rows = (
            db.query(TreatmentRecord.organic)
            .filter(
                TreatmentRecord.field_id == field.id,
                TreatmentRecord.applied_at >= year_start,
                TreatmentRecord.applied_at <= year_end,
            )
            .all()
        )
        treatments_applied = len(treatment_rows)
        treatments_total += treatments_applied
        regen_score: Optional[float] = None
        if treatments_applied > 0:
            organic_count = sum(1 for r in treatment_rows if r.organic)
            regen_score = round(organic_count / treatments_applied * 100, 2)

        has_any = (
            health_rows or ndvi_rows or soil_rows or treatment_rows
        )
        if not has_any:
            continue

        field_entries.append({
            "field_id": field.id,
            "field_name": field.name,
            "avg_health": _round(avg_h),
            "min_health": _round(min_h),
            "max_health": _round(max_h),
            "ndvi_trend": _round(ndvi_trend, 4),
            "soil_ph_delta": _round(soil_ph_delta, 4),
            "treatments_applied": treatments_applied,
            "regen_score": regen_score,
        })

        if avg_h is not None and (best_field_avg is None or avg_h > best_field_avg):
            best_field_avg = avg_h
            best_field_name = field.name

        if health_delta is not None and (
            most_improved_delta is None or health_delta > most_improved_delta
        ):
            most_improved_delta = health_delta
            most_improved_name = field.name

    carbon = compute_carbon_audit(farm, db)
    total_co2e = carbon.get("total_current_co2e_t", 0.0) or 0.0

    return {
        "farm_id": farm.id,
        "year": year,
        "fields": field_entries,
        "best_field": best_field_name,
        "most_improved_field": most_improved_name,
        "total_co2e_sequestered_t": round(total_co2e, 2),
        "treatments_applied_total": treatments_total,
    }
