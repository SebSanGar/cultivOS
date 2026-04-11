"""Seasonal performance benchmark service.

Jalisco season calendar:
  temporal  — June through October  (months 6-10)
  secas     — November through May  (months 11-12, 1-5)

Compares avg HealthScore in the current season vs the immediately prior season
for every field on the farm.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, HealthScore

# Months that belong to each season
_TEMPORAL_MONTHS = {6, 7, 8, 9, 10}
_SECAS_MONTHS = {11, 12, 1, 2, 3, 4, 5}


def _season_of(dt: datetime) -> tuple[str, int]:
    """Return (season_name, season_year) for a datetime.

    season_year is the calendar year in which the season STARTS:
    - temporal 2026 → Jun-Oct 2026
    - secas 2025-26 → Nov 2025 – May 2026  (start year = 2025)
    """
    m = dt.month
    if m in _TEMPORAL_MONTHS:
        return ("temporal", dt.year)
    # secas: Nov-Dec belong to the year they occur; Jan-May belong to prior year's secas
    if m in {11, 12}:
        return ("secas", dt.year)
    # months 1-5: the secas started in the prior year
    return ("secas", dt.year - 1)


def _season_label(name: str, start_year: int) -> str:
    if name == "temporal":
        return f"temporal {start_year}"
    return f"secas {start_year}-{str(start_year + 1)[2:]}"


def _prior_season(name: str, start_year: int) -> tuple[str, int]:
    """Return the immediately preceding season."""
    if name == "temporal":
        # prior to temporal YYYY is secas YYYY-1
        return ("secas", start_year - 1)
    # prior to secas YYYY is temporal YYYY
    return ("temporal", start_year)


def _avg_health_in_season(
    scores: list[HealthScore], season_name: str, season_year: int
) -> float | None:
    vals = [
        float(s.score)
        for s in scores
        if _season_of(s.scored_at) == (season_name, season_year)
    ]
    if not vals:
        return None
    return round(sum(vals) / len(vals), 1)


def compute_seasonal_benchmark(
    farm: Farm, db: Session, reference_date: datetime | None = None
) -> dict:
    now = reference_date or datetime.utcnow()
    cur_name, cur_year = _season_of(now)
    pri_name, pri_year = _prior_season(cur_name, cur_year)

    current_label = _season_label(cur_name, cur_year)
    prior_label = _season_label(pri_name, pri_year)

    fields = db.query(Field).filter(Field.farm_id == farm.id).all()

    field_rows = []
    deltas = []

    for field in fields:
        scores = (
            db.query(HealthScore)
            .filter(HealthScore.field_id == field.id)
            .all()
        )
        cur_avg = _avg_health_in_season(scores, cur_name, cur_year)
        pri_avg = _avg_health_in_season(scores, pri_name, pri_year)

        if cur_avg is not None and pri_avg is not None:
            delta = round(cur_avg - pri_avg, 1)
            improved = delta > 0
            deltas.append(delta)
        else:
            delta = None
            improved = None

        field_rows.append({
            "field_id": field.id,
            "field_name": field.name,
            "current_avg": cur_avg,
            "prior_avg": pri_avg,
            "delta": delta,
            "improved": improved,
        })

    if deltas:
        avg_delta = sum(deltas) / len(deltas)
        if avg_delta > 0:
            overall_trend = "improving"
        elif avg_delta < 0:
            overall_trend = "declining"
        else:
            overall_trend = "stable"
    else:
        overall_trend = "stable"

    return {
        "current_season": current_label,
        "prior_season": prior_label,
        "fields": field_rows,
        "overall_trend": overall_trend,
    }
