"""Farm regional benchmark service.

Compares a farm's average HealthScore against all other farms in the same state.
Returns own_avg_health, state_avg_health (peers only), percentile_rank, and
better_than_pct.

Algorithm:
  1. Compute avg HealthScore for the target farm (across all its fields).
  2. Compute avg HealthScore for every other farm in the same state.
  3. Rank target farm among all farms (including itself) in the state by avg score.
  4. percentile_rank = (rank_from_bottom / total_farms_in_state) * 100
  5. better_than_pct = (peers_beaten / peer_farm_count) * 100
"""

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, HealthScore


def compute_regional_benchmark(farm: Farm, db: Session) -> dict:
    """Return regional benchmark data for the given farm."""

    # Own farm average health (across all fields, all time)
    own_field_ids = [
        row.id
        for row in db.query(Field.id).filter(Field.farm_id == farm.id).all()
    ]
    if own_field_ids:
        own_avg = db.query(func.avg(HealthScore.score)).filter(
            HealthScore.field_id.in_(own_field_ids)
        ).scalar()
    else:
        own_avg = None

    # All other farms in the same state
    peer_farms = (
        db.query(Farm)
        .filter(Farm.state == farm.state, Farm.id != farm.id)
        .all()
    )
    peer_farm_count = len(peer_farms)

    # Compute avg health per peer farm
    peer_avgs: list[float] = []
    for peer in peer_farms:
        peer_field_ids = [
            row.id
            for row in db.query(Field.id).filter(Field.farm_id == peer.id).all()
        ]
        if not peer_field_ids:
            continue
        avg = db.query(func.avg(HealthScore.score)).filter(
            HealthScore.field_id.in_(peer_field_ids)
        ).scalar()
        if avg is not None:
            peer_avgs.append(float(avg))

    # State average (peers only)
    state_avg = (sum(peer_avgs) / len(peer_avgs)) if peer_avgs else None

    # Ranking: how many peers does this farm beat?
    if own_avg is not None:
        beaten = sum(1 for p in peer_avgs if own_avg > p)
        better_than_pct = round((beaten / peer_farm_count) * 100.0, 1) if peer_farm_count else 100.0
        # Percentile rank among all farms in state (including self)
        all_avgs = peer_avgs + [float(own_avg)]
        rank_from_bottom = sum(1 for a in all_avgs if own_avg >= a)
        percentile_rank = round((rank_from_bottom / len(all_avgs)) * 100.0, 1)
    else:
        better_than_pct = 0.0
        percentile_rank = 0.0

    return {
        "farm_id": farm.id,
        "farm_name": farm.name,
        "state": farm.state or "",
        "own_avg_health": round(float(own_avg), 1) if own_avg is not None else None,
        "state_avg_health": round(state_avg, 1) if state_avg is not None else None,
        "percentile_rank": percentile_rank,
        "better_than_pct": better_than_pct,
        "peer_farm_count": peer_farm_count,
    }
