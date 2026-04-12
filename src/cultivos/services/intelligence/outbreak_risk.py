"""Cooperative disease outbreak risk aggregate.

Composes compute_disease_risk_assessment per field across all member farms.
Aggregates: total_high/medium/low_risk_fields, top_risk_crop, affected_farms,
overall_risk_level.
"""

from __future__ import annotations

from collections import Counter

from sqlalchemy.orm import Session

from cultivos.db.models import Cooperative, Field
from cultivos.services.intelligence.disease_risk_assessment import (
    compute_disease_risk_assessment,
)


def compute_outbreak_risk(cooperative: Cooperative, db: Session) -> dict:
    """Aggregate disease outbreak risk across all farms in a cooperative.

    Returns dict with keys matching CoopOutbreakRiskOut schema.
    """
    farms_detail: list[dict] = []
    total_high = 0
    total_medium = 0
    total_low = 0
    affected_farms = 0
    crop_risk_counter: Counter = Counter()  # crop_type → count of high+medium fields

    for farm in cooperative.farms:
        fields = db.query(Field).filter(Field.farm_id == farm.id).all()
        farm_high = 0
        farm_medium = 0
        farm_low = 0

        for field in fields:
            result = compute_disease_risk_assessment(field, db)
            level = result["risk_level"]
            if level == "high":
                farm_high += 1
                crop_risk_counter[field.crop_type] += 1
            elif level == "medium":
                farm_medium += 1
                crop_risk_counter[field.crop_type] += 1
            else:
                farm_low += 1

        total_high += farm_high
        total_medium += farm_medium
        total_low += farm_low

        if farm_high > 0 or farm_medium > 0:
            affected_farms += 1

        farms_detail.append({
            "farm_id": farm.id,
            "farm_name": farm.name,
            "high_risk_fields": farm_high,
            "medium_risk_fields": farm_medium,
            "low_risk_fields": farm_low,
            "total_fields": len(fields),
        })

    # Overall risk level
    if total_high > 0:
        overall_risk_level = "high"
    elif total_medium > 0:
        overall_risk_level = "medium"
    else:
        overall_risk_level = "low"

    # Top risk crop (most high+medium fields)
    top_risk_crop = crop_risk_counter.most_common(1)[0][0] if crop_risk_counter else None

    return {
        "cooperative_id": cooperative.id,
        "total_high_risk_fields": total_high,
        "total_medium_risk_fields": total_medium,
        "total_low_risk_fields": total_low,
        "top_risk_crop": top_risk_crop,
        "affected_farms_count": affected_farms,
        "overall_risk_level": overall_risk_level,
        "farms": farms_detail,
    }
