"""Farm health progress report service.

Compares avg health score, NDVI, and soil pH at start vs end of a date range.

Logic:
- Split period [start_date, end_date] at midpoint
- first_half = [start_date, midpoint)
- second_half = [midpoint, end_date]
- delta = avg(second_half) - avg(first_half)
- improved = health_delta > 0 (None if either half has no health data)
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, HealthScore, NDVIResult, SoilAnalysis


def _avg(values: list[float]) -> Optional[float]:
    return sum(values) / len(values) if values else None


def _delta(first: Optional[float], second: Optional[float]) -> Optional[float]:
    if first is None or second is None:
        return None
    return round(second - first, 4)


def _to_dt(d: date) -> datetime:
    """Convert date to datetime at midnight."""
    return datetime(d.year, d.month, d.day)


def compute_progress_report(farm: Farm, start_date: date, end_date: date, db: Session) -> dict:
    """Return before/after comparison for each field in the farm."""
    mid_date = start_date + (end_date - start_date) / 2
    midpoint = _to_dt(mid_date)
    start_dt = _to_dt(start_date)
    end_dt = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

    # Query all fields for this farm
    fields = db.query(Field).filter(Field.farm_id == farm.id).all()

    field_entries = []
    improved_count = 0
    with_health_count = 0

    for field in fields:
        # ── Health scores ─────────────────────────────────────────────────────
        health_rows = (
            db.query(HealthScore.score, HealthScore.scored_at)
            .filter(
                HealthScore.field_id == field.id,
                HealthScore.scored_at >= start_dt,
                HealthScore.scored_at <= end_dt,
            )
            .all()
        )

        first_health = [r.score for r in health_rows if r.scored_at < midpoint]
        second_health = [r.score for r in health_rows if r.scored_at >= midpoint]
        health_delta = _delta(_avg(first_health), _avg(second_health))

        # ── NDVI ──────────────────────────────────────────────────────────────
        ndvi_rows = (
            db.query(NDVIResult.ndvi_mean, NDVIResult.analyzed_at)
            .filter(
                NDVIResult.field_id == field.id,
                NDVIResult.analyzed_at >= start_dt,
                NDVIResult.analyzed_at <= end_dt,
            )
            .all()
        )

        first_ndvi = [r.ndvi_mean for r in ndvi_rows if r.analyzed_at < midpoint]
        second_ndvi = [r.ndvi_mean for r in ndvi_rows if r.analyzed_at >= midpoint]
        ndvi_delta = _delta(_avg(first_ndvi), _avg(second_ndvi))

        # ── Soil pH ───────────────────────────────────────────────────────────
        soil_rows = (
            db.query(SoilAnalysis.ph, SoilAnalysis.sampled_at)
            .filter(
                SoilAnalysis.field_id == field.id,
                SoilAnalysis.sampled_at >= start_dt,
                SoilAnalysis.sampled_at <= end_dt,
            )
            .all()
        )

        first_ph = [r.ph for r in soil_rows if r.sampled_at < midpoint and r.ph is not None]
        second_ph = [r.ph for r in soil_rows if r.sampled_at >= midpoint and r.ph is not None]
        soil_ph_delta = _delta(_avg(first_ph), _avg(second_ph))

        # Skip fields with no data at all in the period
        if not health_rows and not ndvi_rows and not soil_rows:
            continue

        # ── improved flag ─────────────────────────────────────────────────────
        if health_delta is None:
            improved = None
        else:
            improved = health_delta > 0
            with_health_count += 1
            if improved:
                improved_count += 1

        field_entries.append({
            "field_id": field.id,
            "field_name": field.name,
            "health_delta": health_delta,
            "ndvi_delta": ndvi_delta,
            "soil_ph_delta": soil_ph_delta,
            "improved": improved,
        })

    farms_improved_pct = (
        round(improved_count / with_health_count * 100, 1) if with_health_count > 0 else 0.0
    )

    return {
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
        "fields": field_entries,
        "farms_improved_pct": farms_improved_pct,
    }
