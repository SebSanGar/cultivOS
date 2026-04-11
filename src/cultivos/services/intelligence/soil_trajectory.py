"""Field soil health trajectory service.

Groups SoilAnalysis records by month for the last 6 months (180 days).
Returns avg pH and avg organic_matter_pct per month, sorted oldest→newest.

Trend logic (applied independently to pH and organic_matter):
  improving  — avg of last 2 months > avg of prior 2 months
  declining  — avg of last 2 months < avg of prior 2 months
  stable     — equal, or fewer than 2 monthly data points
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from cultivos.db.models import Field, SoilAnalysis

_WINDOW_DAYS = 180  # 6 months


def _trend(months_data: list[dict], key: str) -> str:
    """Compute trend for a given metric across monthly buckets."""
    values = [m[key] for m in months_data if m[key] is not None]
    if len(values) < 2:
        return "stable"
    # Compare last 2 vs prior 2
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


def compute_soil_trajectory(field: Field, db: Session) -> dict:
    """Return monthly soil health trajectory for the field."""
    cutoff = datetime.utcnow() - timedelta(days=_WINDOW_DAYS)

    records = (
        db.query(SoilAnalysis)
        .filter(
            SoilAnalysis.field_id == field.id,
            SoilAnalysis.sampled_at >= cutoff,
        )
        .order_by(SoilAnalysis.sampled_at)
        .all()
    )

    # Group by YYYY-MM
    buckets: dict[str, list[SoilAnalysis]] = defaultdict(list)
    for r in records:
        label = r.sampled_at.strftime("%Y-%m")
        buckets[label].append(r)

    months = []
    for label in sorted(buckets.keys()):
        recs = buckets[label]
        phs = [r.ph for r in recs if r.ph is not None]
        oms = [r.organic_matter_pct for r in recs if r.organic_matter_pct is not None]
        months.append({
            "month_label": label,
            "avg_ph": round(sum(phs) / len(phs), 2) if phs else None,
            "avg_organic_matter_pct": round(sum(oms) / len(oms), 2) if oms else None,
        })

    return {
        "field_id": field.id,
        "months": months,
        "ph_trend": _trend(months, "avg_ph"),
        "organic_matter_trend": _trend(months, "avg_organic_matter_pct"),
    }
