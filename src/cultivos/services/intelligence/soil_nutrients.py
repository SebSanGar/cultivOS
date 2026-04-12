"""Field soil nutrient trajectory service (#220).

Groups SoilAnalysis records by calendar month for a configurable window
(default 12 months, range 1-24). Returns per-month averages for N/P/K/OM
and independent trends (improving | stable | declining) per nutrient.

Trend logic (same algorithm as #170 soil_trajectory):
  last-2-months-avg vs prior-2-months-avg per nutrient.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from cultivos.db.models import Field, SoilAnalysis


def _trend(months_data: list[dict], key: str) -> str:
    values = [m[key] for m in months_data if m[key] is not None]
    if len(values) < 2:
        return "stable"
    last_2 = values[-2:]
    prior_2 = values[-4:-2] if len(values) >= 4 else values[:-2]
    if not prior_2:
        return "stable"
    avg_last = sum(last_2) / len(last_2)
    avg_prior = sum(prior_2) / len(prior_2)
    if avg_last > avg_prior:
        return "improving"
    if avg_last < avg_prior:
        return "declining"
    return "stable"


def _avg(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 2) if values else None


def compute_soil_nutrients(field: Field, db: Session, months: int = 12) -> dict:
    """Return monthly N/P/K/OM trajectory for the field over the last `months` months."""
    cutoff = datetime.utcnow() - timedelta(days=months * 30)

    records = (
        db.query(SoilAnalysis)
        .filter(
            SoilAnalysis.field_id == field.id,
            SoilAnalysis.sampled_at >= cutoff,
        )
        .order_by(SoilAnalysis.sampled_at)
        .all()
    )

    buckets: dict[str, list[SoilAnalysis]] = defaultdict(list)
    for r in records:
        buckets[r.sampled_at.strftime("%Y-%m")].append(r)

    monthly = []
    for label in sorted(buckets.keys()):
        recs = buckets[label]
        ns = [r.nitrogen_ppm for r in recs if r.nitrogen_ppm is not None]
        ps = [r.phosphorus_ppm for r in recs if r.phosphorus_ppm is not None]
        ks = [r.potassium_ppm for r in recs if r.potassium_ppm is not None]
        oms = [r.organic_matter_pct for r in recs if r.organic_matter_pct is not None]
        monthly.append({
            "month_label": label,
            "avg_nitrogen_ppm": _avg(ns),
            "avg_phosphorus_ppm": _avg(ps),
            "avg_potassium_ppm": _avg(ks),
            "avg_organic_matter_pct": _avg(oms),
        })

    return {
        "field_id": field.id,
        "window_months": months,
        "months": monthly,
        "nitrogen_trend": _trend(monthly, "avg_nitrogen_ppm"),
        "phosphorus_trend": _trend(monthly, "avg_phosphorus_ppm"),
        "potassium_trend": _trend(monthly, "avg_potassium_ppm"),
        "organic_matter_trend": _trend(monthly, "avg_organic_matter_pct"),
    }
