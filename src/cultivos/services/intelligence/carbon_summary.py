"""Cooperative-level carbon sequestration summary service.

Aggregates CarbonBaseline data across all member farms in a cooperative.
Composes compute_carbon_audit per farm and sums totals.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from cultivos.db.models import Cooperative, Farm
from cultivos.services.intelligence.carbon import (
    _HIGH_CONFIDENCE_METHODS,
    _MEDIUM_CONFIDENCE_METHODS,
    compute_carbon_projection,
)
from cultivos.services.intelligence.carbon_audit import compute_carbon_audit


def _majority_confidence(confidence_counts: dict[str, int]) -> str:
    """Return the confidence tier with the highest count.

    Tie-breaks: high > medium > low. If no data, return 'low'.
    """
    if not confidence_counts or sum(confidence_counts.values()) == 0:
        return "low"
    for tier in ("high", "medium", "low"):
        if confidence_counts.get(tier, 0) == max(confidence_counts.values()):
            return tier
    return "low"


def compute_coop_carbon_summary(cooperative: Cooperative, db: Session) -> dict:
    """Aggregate carbon sequestration metrics across all member farms.

    Returns:
        cooperative_id, total_co2e_baseline_t, total_projected_5yr_t,
        avg_confidence, fields_with_data_count, fields_total_count
    """
    farms = db.query(Farm).filter(Farm.cooperative_id == cooperative.id).all()

    total_co2e = 0.0
    total_projected = 0.0
    fields_with_data = 0
    fields_total = 0
    confidence_counts: dict[str, int] = {"high": 0, "medium": 0, "low": 0}

    for farm in farms:
        audit = compute_carbon_audit(farm, db)
        total_co2e += audit["total_current_co2e_t"]
        total_projected += audit["total_projected_5yr_co2e_t"]
        fields_with_data += audit["fields_with_baseline"]
        fields_total += audit["total_fields"]

        # Determine confidence tier for each field with baseline
        # We need to re-query baselines to get lab_method per field
        # Re-use the existing carbon_audit approach: just count confidence from projection

    # Re-derive avg_confidence from per-field baselines
    from cultivos.db.models import CarbonBaseline, Field
    from sqlalchemy import and_, func

    for farm in farms:
        field_ids = [
            fid for (fid,) in db.query(Field.id).filter(Field.farm_id == farm.id).all()
        ]
        if not field_ids:
            continue

        # Latest baseline per field
        latest_sub = (
            db.query(
                CarbonBaseline.field_id,
                func.max(CarbonBaseline.recorded_at).label("max_recorded"),
            )
            .filter(CarbonBaseline.field_id.in_(field_ids))
            .group_by(CarbonBaseline.field_id)
            .subquery()
        )
        baselines = (
            db.query(CarbonBaseline)
            .join(
                latest_sub,
                and_(
                    CarbonBaseline.field_id == latest_sub.c.field_id,
                    CarbonBaseline.recorded_at == latest_sub.c.max_recorded,
                ),
            )
            .all()
        )

        for cb in baselines:
            method = cb.lab_method.strip().lower()
            if method in _HIGH_CONFIDENCE_METHODS:
                confidence_counts["high"] += 1
            elif method in _MEDIUM_CONFIDENCE_METHODS:
                confidence_counts["medium"] += 1
            else:
                confidence_counts["low"] += 1

    avg_conf = _majority_confidence(confidence_counts) if fields_with_data > 0 else "low"

    return {
        "cooperative_id": cooperative.id,
        "total_co2e_baseline_t": round(total_co2e, 2),
        "total_projected_5yr_t": round(total_projected, 2),
        "avg_confidence": avg_conf,
        "fields_with_data_count": fields_with_data,
        "fields_total_count": fields_total,
    }
