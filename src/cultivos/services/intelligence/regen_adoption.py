"""Cooperative regenerative practice adoption rate service.

GET /api/cooperatives/{coop_id}/regen-adoption?days=30

For each member farm:
- regen_score: most recent month's regen_score from compute_regen_trajectory (0.0 if no data)
- treatment_count: total TreatmentRecords created in the last `days` calendar days

overall_regen_score_avg: mean of farm regen_scores (0.0 when no farms).
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from cultivos.db.models import Cooperative, Farm, Field, TreatmentRecord
from cultivos.services.intelligence.regen_trajectory import compute_regen_trajectory


def compute_regen_adoption(coop: Cooperative, days: int, db: Session) -> dict:
    """Return regen adoption stats for all member farms in a cooperative."""
    farms = db.query(Farm).filter(Farm.cooperative_id == coop.id).all()

    if not farms:
        return {
            "cooperative_id": coop.id,
            "period_days": days,
            "overall_regen_score_avg": 0.0,
            "farms": [],
        }

    cutoff = datetime.utcnow() - timedelta(days=days)
    farm_entries = []

    for farm in farms:
        field_ids = [
            f.id
            for f in db.query(Field.id).filter(Field.farm_id == farm.id).all()
        ]

        # TreatmentRecord count within the period
        if field_ids:
            treatment_count = (
                db.query(TreatmentRecord)
                .filter(
                    TreatmentRecord.field_id.in_(field_ids),
                    TreatmentRecord.created_at >= cutoff,
                )
                .count()
            )
        else:
            treatment_count = 0

        # regen_score: latest month's score from trajectory
        trajectory = compute_regen_trajectory(farm, db)
        months = trajectory.get("months", [])
        regen_score = months[-1]["regen_score"] if months else 0.0

        farm_entries.append({
            "farm_id": farm.id,
            "farm_name": farm.name,
            "regen_score": round(regen_score, 2),
            "treatment_count": treatment_count,
        })

    scores = [e["regen_score"] for e in farm_entries]
    overall_avg = round(sum(scores) / len(scores), 2) if scores else 0.0

    return {
        "cooperative_id": coop.id,
        "period_days": days,
        "overall_regen_score_avg": overall_avg,
        "farms": farm_entries,
    }
