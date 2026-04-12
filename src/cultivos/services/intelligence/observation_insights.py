"""#190 Farmer observation insights — aggregate FarmerObservation rows per farm.

Counts by type, computes percentages, identifies last observation date.
Used to surface farmer engagement and most-reported field conditions for
FODECIJAL grant narrative ("farmers are actively documenting field state").
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from cultivos.db.models import Farm, FarmerObservation, Field


def compute_observation_insights(farm: Farm, days: int, db: Session) -> dict:
    """Aggregate farmer observations across all fields in a farm.

    Returns dict matching ObservationInsightsOut schema:
    - total_observations: count in period
    - observations_by_type: [{type, count, pct}] sorted DESC by count
    - last_observed_at: most recent created_at (global, unfiltered by period) or None
    - period_days: echoed from input
    """
    cutoff = datetime.utcnow() - timedelta(days=days)

    rows = (
        db.query(FarmerObservation)
        .join(Field, FarmerObservation.field_id == Field.id)
        .filter(Field.farm_id == farm.id)
        .filter(FarmerObservation.created_at >= cutoff)
        .all()
    )

    counts: Counter = Counter(r.observation_type for r in rows)
    total = sum(counts.values())

    by_type = [
        {
            "type": obs_type,
            "count": count,
            "pct": round(count / total * 100, 2) if total else 0.0,
        }
        for obs_type, count in counts.most_common()
    ]

    last_row = (
        db.query(FarmerObservation)
        .join(Field, FarmerObservation.field_id == Field.id)
        .filter(Field.farm_id == farm.id)
        .order_by(FarmerObservation.created_at.desc())
        .first()
    )

    return {
        "farm_id": farm.id,
        "period_days": days,
        "total_observations": total,
        "observations_by_type": by_type,
        "last_observed_at": last_row.created_at if last_row else None,
    }
