"""Cooperative weekly action plan aggregate.

Composes compose_action_plan per field across all member farms in a
cooperative, flattens the actions, enriches each with farm/field context,
and returns them priority-sorted (high→medium→low).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from cultivos.db.models import Cooperative, Farm, Field
from cultivos.services.intelligence.action_plan import compose_action_plan

_PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


def compute_coop_action_plan(
    coop: Cooperative,
    days: int,
    limit: int,
    db: Session,
) -> dict:
    """Aggregate action plans across all member farm fields."""
    farms = db.query(Farm).filter(Farm.cooperative_id == coop.id).all()

    enriched: list[dict] = []
    total_fields_scanned = 0

    for farm in farms:
        fields = db.query(Field).filter(Field.farm_id == farm.id).all()
        for field in fields:
            total_fields_scanned += 1
            plan = compose_action_plan(field, days, db)
            for action in plan.get("actions", []):
                enriched.append(
                    {
                        "farm_id": farm.id,
                        "farm_name": farm.name,
                        "field_id": field.id,
                        "crop_type": field.crop_type,
                        "priority": action["priority"],
                        "category": action["category"],
                        "action_es": action["action_es"],
                        "source_es": action["source_es"],
                    }
                )

    enriched.sort(key=lambda a: _PRIORITY_RANK[a["priority"]])

    total_actions = len(enriched)
    high_count = sum(1 for a in enriched if a["priority"] == "high")
    medium_count = sum(1 for a in enriched if a["priority"] == "medium")
    low_count = sum(1 for a in enriched if a["priority"] == "low")

    return {
        "cooperative_id": coop.id,
        "period_days": days,
        "total_fields_scanned": total_fields_scanned,
        "total_actions": total_actions,
        "high_count": high_count,
        "medium_count": medium_count,
        "low_count": low_count,
        "actions": enriched[:limit],
    }
