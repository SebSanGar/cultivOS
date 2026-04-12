"""Cooperative regen trajectory aggregate.

Composes compute_regen_trajectory per member farm, merges monthly regen scores
across farms into a cooperative-wide longitudinal series. Reuses the farm-level
trend threshold (5pt delta, first-3 vs last-3 months) for the overall trend.
"""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session

from cultivos.db.models import Cooperative
from cultivos.services.intelligence.regen_trajectory import compute_regen_trajectory

_TREND_THRESHOLD = 5.0


def compute_coop_regen_trajectory(cooperative: Cooperative, db: Session) -> dict:
    """Aggregate monthly regen trajectory across all member farms."""
    farm_entries: list[dict] = []
    month_accumulator: dict[str, list[float]] = defaultdict(list)

    for farm in cooperative.farms:
        traj = compute_regen_trajectory(farm, db)
        months = traj.get("months", [])

        for m in months:
            month_accumulator[m["month"]].append(float(m["regen_score"]))

        latest = round(float(months[-1]["regen_score"]), 2) if months else 0.0
        farm_entries.append({
            "farm_id": farm.id,
            "farm_name": farm.name,
            "months_count": len(months),
            "latest_regen_score": latest,
            "trend": traj.get("trend", "stable"),
        })

    overall_months = [
        {
            "month": key,
            "avg_regen_score": round(sum(scores) / len(scores), 2),
            "farms_contributing": len(scores),
        }
        for key, scores in sorted(month_accumulator.items())
    ]

    overall_trend = _compute_overall_trend(overall_months)

    return {
        "cooperative_id": cooperative.id,
        "overall_months": overall_months,
        "overall_trend": overall_trend,
        "farms_count": len(farm_entries),
        "farms": farm_entries,
    }


def _compute_overall_trend(months: list[dict]) -> str:
    if len(months) < 6:
        return "stable"
    first_avg = sum(m["avg_regen_score"] for m in months[:3]) / 3
    last_avg = sum(m["avg_regen_score"] for m in months[-3:]) / 3
    delta = last_avg - first_avg
    if delta > _TREND_THRESHOLD:
        return "improving"
    if delta < -_TREND_THRESHOLD:
        return "declining"
    return "stable"
