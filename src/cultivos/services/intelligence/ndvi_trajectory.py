"""Field NDVI trajectory service.

Groups NDVIResult records by month for the last 90 days.
Returns avg ndvi_mean and avg stress_pct per month, sorted oldest→newest.

Trend logic:
  ndvi_trend — avg NDVI of last 2 months vs prior 2 months
    improving: last > prior, declining: last < prior, else stable
  stress_trend — lower stress is better, so direction is inverted
    improving: last < prior, declining: last > prior, else stable
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from cultivos.db.models import Field, NDVIResult

_WINDOW_DAYS = 90


def _direction(months_data: list[dict], key: str, higher_is_better: bool) -> str:
    values = [m[key] for m in months_data if m[key] is not None]
    if len(values) < 2:
        return "stable"
    last_2 = values[-2:]
    prior_2 = values[-4:-2] if len(values) >= 4 else values[:-2]
    if not prior_2:
        return "stable"
    avg_last = sum(last_2) / len(last_2)
    avg_prior = sum(prior_2) / len(prior_2)
    if avg_last == avg_prior:
        return "stable"
    increased = avg_last > avg_prior
    if higher_is_better:
        return "improving" if increased else "declining"
    return "declining" if increased else "improving"


def compute_ndvi_trajectory(field: Field, db: Session) -> dict:
    """Return monthly NDVI trajectory for the field over the last 90 days."""
    cutoff = datetime.utcnow() - timedelta(days=_WINDOW_DAYS)

    records = (
        db.query(NDVIResult)
        .filter(
            NDVIResult.field_id == field.id,
            NDVIResult.analyzed_at >= cutoff,
        )
        .order_by(NDVIResult.analyzed_at)
        .all()
    )

    buckets: dict[str, list[NDVIResult]] = defaultdict(list)
    for r in records:
        label = r.analyzed_at.strftime("%Y-%m")
        buckets[label].append(r)

    months = []
    for label in sorted(buckets.keys()):
        recs = buckets[label]
        ndvis = [r.ndvi_mean for r in recs if r.ndvi_mean is not None]
        stresses = [r.stress_pct for r in recs if r.stress_pct is not None]
        months.append({
            "month_label": label,
            "avg_ndvi": round(sum(ndvis) / len(ndvis), 3) if ndvis else None,
            "avg_stress_pct": round(sum(stresses) / len(stresses), 2) if stresses else None,
        })

    return {
        "field_id": field.id,
        "months": months,
        "ndvi_trend": _direction(months, "avg_ndvi", higher_is_better=True),
        "stress_trend": _direction(months, "avg_stress_pct", higher_is_better=False),
    }
