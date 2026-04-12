"""Cooperative monthly progress snapshot service.

Aggregates HealthScore + TreatmentRecord + FarmerObservation across all
member-farm fields by YYYY-MM for the last N months. Computes regen_score
per month using the shared formula: organic_pct*0.6 + avg_health*0.4.

Trend compares last-half vs first-half avg regen_score:
  >5.0  → improving
  <-5.0 → declining
  else  → stable
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from cultivos.db.models import (
    Farm,
    FarmerObservation,
    Field,
    HealthScore,
    TreatmentRecord,
)

_TREND_THRESHOLD = 5.0


def compute_coop_monthly_progress(coop_id: int, months: int, db: Session) -> dict:
    cutoff = datetime.utcnow() - timedelta(days=months * 31)

    farm_ids = [
        fid for (fid,) in db.query(Farm.id)
        .filter(Farm.cooperative_id == coop_id)
        .all()
    ]

    if not farm_ids:
        return {
            "cooperative_id": coop_id,
            "months_requested": months,
            "months": [],
            "overall_trend": "stable",
        }

    field_ids = [
        fid for (fid,) in db.query(Field.id)
        .filter(Field.farm_id.in_(farm_ids))
        .all()
    ]

    if not field_ids:
        return {
            "cooperative_id": coop_id,
            "months_requested": months,
            "months": [],
            "overall_trend": "stable",
        }

    health_by_month: dict[str, list[float]] = defaultdict(list)
    for scored_at, score in (
        db.query(HealthScore.scored_at, HealthScore.score)
        .filter(HealthScore.field_id.in_(field_ids))
        .filter(HealthScore.scored_at >= cutoff)
        .all()
    ):
        if scored_at is not None:
            health_by_month[scored_at.strftime("%Y-%m")].append(float(score))

    treatments_by_month: dict[str, dict] = defaultdict(
        lambda: {"total": 0, "organic": 0}
    )
    for created_at, organic in (
        db.query(TreatmentRecord.created_at, TreatmentRecord.organic)
        .filter(TreatmentRecord.field_id.in_(field_ids))
        .filter(TreatmentRecord.created_at >= cutoff)
        .all()
    ):
        if created_at is not None:
            key = created_at.strftime("%Y-%m")
            treatments_by_month[key]["total"] += 1
            if organic:
                treatments_by_month[key]["organic"] += 1

    obs_by_month: dict[str, int] = defaultdict(int)
    for (created_at,) in (
        db.query(FarmerObservation.created_at)
        .filter(FarmerObservation.field_id.in_(field_ids))
        .filter(FarmerObservation.created_at >= cutoff)
        .all()
    ):
        if created_at is not None:
            obs_by_month[created_at.strftime("%Y-%m")] += 1

    all_months = (
        set(health_by_month.keys())
        | set(treatments_by_month.keys())
        | set(obs_by_month.keys())
    )

    if not all_months:
        return {
            "cooperative_id": coop_id,
            "months_requested": months,
            "months": [],
            "overall_trend": "stable",
        }

    entries: list[dict] = []
    prev_regen: float | None = None
    for key in sorted(all_months):
        scores = health_by_month.get(key, [])
        avg_health = sum(scores) / len(scores) if scores else 0.0

        t = treatments_by_month.get(key, {"total": 0, "organic": 0})
        total = t["total"]
        organic_pct = (t["organic"] / total * 100.0) if total > 0 else 0.0
        regen = (organic_pct * 0.6) + (avg_health * 0.4)

        mom_delta = 0.0 if prev_regen is None else regen - prev_regen
        prev_regen = regen

        entries.append({
            "month": key,
            "avg_health": round(avg_health, 2),
            "total_treatments": total,
            "new_observations": obs_by_month.get(key, 0),
            "regen_score_avg": round(regen, 2),
            "mom_delta": round(mom_delta, 2),
        })

    return {
        "cooperative_id": coop_id,
        "months_requested": months,
        "months": entries,
        "overall_trend": _trend(entries),
    }


def _trend(entries: list[dict]) -> str:
    if len(entries) < 2:
        return "stable"
    mid = len(entries) // 2
    first = entries[:mid] or entries[:1]
    last = entries[mid:] or entries[-1:]
    first_avg = sum(e["regen_score_avg"] for e in first) / len(first)
    last_avg = sum(e["regen_score_avg"] for e in last) / len(last)
    delta = last_avg - first_avg
    if delta > _TREND_THRESHOLD:
        return "improving"
    if delta < -_TREND_THRESHOLD:
        return "declining"
    return "stable"
