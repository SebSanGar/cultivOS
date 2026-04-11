"""Cooperative member farm ranking service.

Ranks member farms by composite score:
  health_avg (40%) + regen_score (30%) + alert_response_rate (30%)
"""

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from cultivos.db.models import Cooperative, Farm, Field, HealthScore
from cultivos.services.intelligence.alert_effectiveness import compute_alert_effectiveness
from cultivos.services.intelligence.regen_trajectory import compute_regen_trajectory


def _latest_health_avg(farm: Farm, db: Session) -> float:
    """Average of latest HealthScore per field across all fields in the farm."""
    field_ids = [f.id for f in db.query(Field.id).filter(Field.farm_id == farm.id).all()]
    if not field_ids:
        return 0.0

    latest_sub = (
        db.query(
            HealthScore.field_id,
            func.max(HealthScore.scored_at).label("max_scored"),
        )
        .filter(HealthScore.field_id.in_(field_ids))
        .group_by(HealthScore.field_id)
        .subquery()
    )
    latest_scores = (
        db.query(HealthScore)
        .join(
            latest_sub,
            and_(
                HealthScore.field_id == latest_sub.c.field_id,
                HealthScore.scored_at == latest_sub.c.max_scored,
            ),
        )
        .all()
    )
    if not latest_scores:
        return 0.0
    return round(sum(hs.score for hs in latest_scores) / len(latest_scores), 1)


def _latest_regen_score(farm: Farm, db: Session) -> float:
    """Most recent monthly regen_score from regen_trajectory (0.0 if no data)."""
    traj = compute_regen_trajectory(farm, db)
    months = traj.get("months", [])
    if not months:
        return 0.0
    return round(months[-1].get("regen_score", 0.0), 1)


def compute_member_ranking(cooperative: Cooperative, db: Session) -> dict:
    """Rank all member farms by composite score."""
    farms = db.query(Farm).filter(Farm.cooperative_id == cooperative.id).all()

    members = []
    for farm in farms:
        health_avg = _latest_health_avg(farm, db)

        regen_score = _latest_regen_score(farm, db)

        effectiveness = compute_alert_effectiveness(farm, db)
        alert_response_rate = effectiveness.get("improvement_rate_pct", 0.0)

        composite_score = round(
            health_avg * 0.4 + regen_score * 0.3 + alert_response_rate * 0.3,
            1,
        )

        members.append({
            "farm_id": farm.id,
            "farm_name": farm.name,
            "composite_score": composite_score,
            "rank": 0,  # assigned below
            "health_avg": health_avg,
            "regen_score": regen_score,
            "alert_response_rate": alert_response_rate,
        })

    # Sort descending and assign rank
    members.sort(key=lambda m: m["composite_score"], reverse=True)
    for i, member in enumerate(members):
        member["rank"] = i + 1

    return {
        "cooperative_id": cooperative.id,
        "members": members,
    }
