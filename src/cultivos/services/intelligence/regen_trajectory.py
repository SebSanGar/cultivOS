"""Regenerative score improvement trajectory service.

Computes monthly regen score over the last 12 months for a farm.

regen_score per month = (organic_treatment_pct * 0.6) + (avg_health_score * 0.4)

trend:
  improving  — last 3 months avg regen_score > first 3 months by > 5 points
  declining  — last 3 months avg regen_score < first 3 months by > 5 points
  stable     — difference <= 5, or fewer than 6 months of data
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord

_TREND_THRESHOLD = 5.0   # regen_score delta to declare improving/declining


def compute_regen_trajectory(farm: Farm, db: Session) -> dict:
    """Return monthly regen trajectory for all fields in a farm.

    Returns a dict with keys: farm_id, months, trend
    """
    field_ids = [f.id for f in db.query(Field.id).filter(Field.farm_id == farm.id).all()]

    if not field_ids:
        return {"farm_id": farm.id, "months": [], "trend": "stable"}

    # ── Health scores grouped by YYYY-MM ─────────────────────────────────────
    health_rows = (
        db.query(HealthScore.scored_at, HealthScore.score)
        .filter(HealthScore.field_id.in_(field_ids))
        .all()
    )

    health_by_month: dict[str, list[float]] = defaultdict(list)
    for scored_at, score in health_rows:
        if scored_at is not None:
            key = scored_at.strftime("%Y-%m")
            health_by_month[key].append(score)

    # ── Treatment records grouped by YYYY-MM ──────────────────────────────────
    treatment_rows = (
        db.query(TreatmentRecord.created_at, TreatmentRecord.organic)
        .filter(TreatmentRecord.field_id.in_(field_ids))
        .all()
    )

    treatment_by_month: dict[str, dict] = defaultdict(lambda: {"total": 0, "organic": 0})
    for created_at, organic in treatment_rows:
        if created_at is not None:
            key = created_at.strftime("%Y-%m")
            treatment_by_month[key]["total"] += 1
            if organic:
                treatment_by_month[key]["organic"] += 1

    # ── Merge all months ──────────────────────────────────────────────────────
    all_months = set(health_by_month.keys()) | set(treatment_by_month.keys())

    if not all_months:
        return {"farm_id": farm.id, "months": [], "trend": "stable"}

    month_entries = []
    for month_key in sorted(all_months):
        health_scores = health_by_month.get(month_key, [])
        avg_health = sum(health_scores) / len(health_scores) if health_scores else 0.0

        t = treatment_by_month.get(month_key, {"total": 0, "organic": 0})
        total = t["total"]
        organic_pct = (t["organic"] / total * 100.0) if total > 0 else 0.0

        regen_score = (organic_pct * 0.6) + (avg_health * 0.4)

        month_entries.append({
            "month": month_key,
            "organic_treatment_pct": round(organic_pct, 2),
            "avg_health_score": round(avg_health, 2),
            "treatment_count": total,
            "regen_score": round(regen_score, 2),
        })

    # ── Trend calculation ─────────────────────────────────────────────────────
    trend = _compute_trend(month_entries)

    return {
        "farm_id": farm.id,
        "months": month_entries,
        "trend": trend,
    }


def _compute_trend(months: list[dict]) -> str:
    """Compare last 3 vs first 3 months avg regen_score."""
    if len(months) < 6:
        return "stable"

    first_3 = months[:3]
    last_3 = months[-3:]

    first_avg = sum(m["regen_score"] for m in first_3) / 3
    last_avg = sum(m["regen_score"] for m in last_3) / 3

    delta = last_avg - first_avg
    if delta > _TREND_THRESHOLD:
        return "improving"
    if delta < -_TREND_THRESHOLD:
        return "declining"
    return "stable"
