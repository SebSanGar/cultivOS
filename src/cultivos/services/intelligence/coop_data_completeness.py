"""Cooperative data completeness aggregate service.

Composes compute_data_completeness(db, farm_id) per member farm and rolls up
to cooperative level. Returns overall avg score, worst_farm, and per-grade
counts (A >=80, B 60-79, C 40-59, D <40).
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from cultivos.db.models import Farm
from cultivos.services.intelligence.completeness import compute_data_completeness


def _grade(score: float) -> str:
    if score >= 80:
        return "A"
    if score >= 60:
        return "B"
    if score >= 40:
        return "C"
    return "D"


def compute_coop_data_completeness(coop_id: int, db: Session) -> dict:
    farms = (
        db.query(Farm)
        .filter(Farm.cooperative_id == coop_id)
        .order_by(Farm.id)
        .all()
    )

    grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0}
    scores: list[float] = []
    worst_farm: Optional[dict] = None
    worst_score: Optional[float] = None

    for farm in farms:
        result = compute_data_completeness(db, farm.id)
        score = float(result.get("farm_score") or 0.0)
        scores.append(score)
        grade_counts[_grade(score)] += 1
        if worst_score is None or score < worst_score:
            worst_score = score
            worst_farm = {
                "farm_id": farm.id,
                "farm_name": farm.name,
                "farm_score": round(score, 1),
            }

    overall = round(sum(scores) / len(scores), 1) if scores else 0.0

    return {
        "cooperative_id": coop_id,
        "total_farms": len(farms),
        "overall_completeness_pct": overall,
        "worst_farm": worst_farm,
        "farms_by_grade": grade_counts,
    }
