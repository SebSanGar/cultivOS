"""Cooperative 30-day health prediction aggregate.

Composes compute_health_prediction per field across all member farms,
rolls up to farm-level and cooperative-level summaries.
"""

from __future__ import annotations

from collections import Counter

from sqlalchemy.orm import Session

from cultivos.db.models import Cooperative
from cultivos.services.intelligence.health_prediction import compute_health_prediction


def _majority_trend(trends: list[str]) -> str:
    if not trends:
        return "stable"
    counts = Counter(trends)
    return counts.most_common(1)[0][0]


def compute_coop_health_prediction(cooperative: Cooperative, db: Session) -> dict:
    """Aggregate 30-day health prediction across all member farm fields."""
    coop_current_vals: list[float] = []
    coop_predicted_vals: list[float] = []
    coop_at_risk = 0
    coop_fields_count = 0
    coop_fields_with_data = 0
    coop_trend_counts = {"improving": 0, "stable": 0, "declining": 0}

    farm_entries: list[dict] = []
    top_declining: dict | None = None

    for farm in cooperative.farms:
        fields = list(farm.fields)
        farm_fields_count = len(fields)
        farm_current_vals: list[float] = []
        farm_predicted_vals: list[float] = []
        farm_at_risk = 0
        farm_trends: list[str] = []
        farm_fields_with_data = 0

        for field in fields:
            pred = compute_health_prediction(field, db)
            if pred["data_points"] == 0:
                continue
            farm_fields_with_data += 1
            farm_current_vals.append(float(pred["current_avg_health"]))
            farm_predicted_vals.append(float(pred["predicted_health_30d"]))
            if pred["risk_flag"]:
                farm_at_risk += 1
            farm_trends.append(pred["trend_direction"])
            coop_trend_counts[pred["trend_direction"]] += 1

        coop_fields_count += farm_fields_count
        coop_fields_with_data += farm_fields_with_data
        coop_current_vals.extend(farm_current_vals)
        coop_predicted_vals.extend(farm_predicted_vals)
        coop_at_risk += farm_at_risk

        farm_avg_current = (
            round(sum(farm_current_vals) / len(farm_current_vals), 2)
            if farm_current_vals
            else 0.0
        )
        farm_avg_predicted = (
            round(sum(farm_predicted_vals) / len(farm_predicted_vals), 2)
            if farm_predicted_vals
            else 0.0
        )
        farm_trend = _majority_trend(farm_trends)

        farm_entries.append({
            "farm_id": farm.id,
            "farm_name": farm.name,
            "fields_count": farm_fields_count,
            "fields_with_data": farm_fields_with_data,
            "avg_current_health": farm_avg_current,
            "avg_predicted_30d": farm_avg_predicted,
            "fields_at_risk": farm_at_risk,
            "trend": farm_trend,
        })

        if farm_fields_with_data > 0:
            delta = round(farm_avg_predicted - farm_avg_current, 2)
            if top_declining is None or delta < top_declining["delta"]:
                top_declining = {
                    "farm_id": farm.id,
                    "farm_name": farm.name,
                    "delta": delta,
                }

    avg_current = (
        round(sum(coop_current_vals) / len(coop_current_vals), 2)
        if coop_current_vals
        else 0.0
    )
    avg_predicted = (
        round(sum(coop_predicted_vals) / len(coop_predicted_vals), 2)
        if coop_predicted_vals
        else 0.0
    )
    projected_delta = round(avg_predicted - avg_current, 2)

    # Only surface top_declining_farm if it's actually declining (negative delta)
    if top_declining is not None and top_declining["delta"] >= 0:
        top_declining = None

    return {
        "cooperative_id": cooperative.id,
        "fields_count": coop_fields_count,
        "fields_with_data": coop_fields_with_data,
        "avg_current_health": avg_current,
        "avg_predicted_health_30d": avg_predicted,
        "projected_delta": projected_delta,
        "fields_at_risk_count": coop_at_risk,
        "trend_distribution": coop_trend_counts,
        "top_declining_farm": top_declining,
        "farms": farm_entries,
    }
