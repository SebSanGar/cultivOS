"""Cooperative crop diversity score service.

Aggregates Field crop_type distribution (weighted by hectares) across every
farm in a cooperative. Produces distinct-crop counts (coop + per-farm), the
Shannon diversity index over coop-level crop proportions, and the top 3 crops
by total hectares.

Shannon formula: H = -sum(p_i * ln(p_i)) where p_i is the hectare share of
crop i. Single crop → 0.0. Fields with zero/None hectares contribute to
distinct-crop counts but not to Shannon or top_crops.
"""

from __future__ import annotations

import math

from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field


def compute_coop_crop_diversity(coop_id: int, db: Session) -> dict:
    farms = db.query(Farm).filter(Farm.cooperative_id == coop_id).order_by(Farm.id).all()

    total_hectares_by_crop: dict[str, float] = {}
    distinct_crops_coop: set[str] = set()
    farm_entries: list[dict] = []
    total_fields = 0

    for farm in farms:
        fields = db.query(Field).filter(Field.farm_id == farm.id).order_by(Field.id).all()
        total_fields += len(fields)
        farm_crops: set[str] = set()
        for field in fields:
            crop = field.crop_type
            if not crop:
                continue
            farm_crops.add(crop)
            distinct_crops_coop.add(crop)
            hectares = float(field.hectares or 0.0)
            if hectares > 0:
                total_hectares_by_crop[crop] = total_hectares_by_crop.get(crop, 0.0) + hectares
        farm_entries.append(
            {
                "farm_id": farm.id,
                "farm_name": farm.name,
                "distinct_crops": len(farm_crops),
                "crop_types": sorted(farm_crops),
            }
        )

    total_hectares = sum(total_hectares_by_crop.values())
    shannon = 0.0
    if total_hectares > 0 and len(total_hectares_by_crop) > 1:
        for ha in total_hectares_by_crop.values():
            p = ha / total_hectares
            if p > 0:
                shannon -= p * math.log(p)

    ranked = sorted(
        total_hectares_by_crop.items(),
        key=lambda kv: (-kv[1], kv[0]),
    )
    top_crops: list[dict] = []
    for crop, ha in ranked[:3]:
        pct = (ha / total_hectares * 100.0) if total_hectares > 0 else 0.0
        top_crops.append({"crop_type": crop, "hectares": round(ha, 4), "pct": round(pct, 4)})

    return {
        "cooperative_id": coop_id,
        "total_farms": len(farms),
        "total_fields": total_fields,
        "distinct_crops_coop": len(distinct_crops_coop),
        "shannon_index": round(shannon, 4),
        "top_crops": top_crops,
        "farms": farm_entries,
    }
