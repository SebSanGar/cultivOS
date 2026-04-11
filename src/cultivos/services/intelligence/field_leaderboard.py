"""Cooperative field health leaderboard service.

Flattens all fields across all member farms in a cooperative, fetches the
latest HealthScore per field, and ranks them descending by health (nulls last).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from cultivos.db.models import Cooperative, Farm, Field, HealthScore
from cultivos.models.field_leaderboard import FieldLeaderboardEntry, FieldLeaderboardOut


def compute_field_leaderboard(coop: Cooperative, db: Session) -> FieldLeaderboardOut:
    """Return all fields in the cooperative ranked by latest health score."""
    farms = db.query(Farm).filter(Farm.cooperative_id == coop.id).all()

    entries: list[FieldLeaderboardEntry] = []
    for farm in farms:
        fields = db.query(Field).filter(Field.farm_id == farm.id).all()
        for field in fields:
            latest = (
                db.query(HealthScore)
                .filter(HealthScore.field_id == field.id)
                .order_by(HealthScore.scored_at.desc())
                .first()
            )
            entries.append(
                FieldLeaderboardEntry(
                    rank=0,  # assigned after sorting
                    farm_name=farm.name,
                    field_id=field.id,
                    crop_type=field.crop_type,
                    latest_health=round(latest.score, 1) if latest else None,
                    hectares=field.hectares or 0.0,
                )
            )

    # Sort: scored fields first (desc), then nulls
    entries.sort(key=lambda e: (e.latest_health is None, -(e.latest_health or 0)))

    # Assign sequential ranks
    for i, entry in enumerate(entries, start=1):
        entry.rank = i

    return FieldLeaderboardOut(
        cooperative_id=coop.id,
        total_fields=len(entries),
        fields=entries,
    )
