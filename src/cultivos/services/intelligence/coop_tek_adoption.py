"""Cooperative TEK practice adoption rate.

Composes compute_tek_alignment per field across all member farms, aggregates
alignment scores per farm and cooperative-wide, and identifies the most-supported
traditional practice by sensor-backed count.
"""

from __future__ import annotations

from collections import Counter
from datetime import date

from sqlalchemy.orm import Session

from cultivos.db.models import Cooperative, Field
from cultivos.services.intelligence.tek_alignment import compute_tek_alignment


def compute_coop_tek_adoption(
    cooperative: Cooperative,
    month: int | None,
    db: Session,
) -> dict:
    """Aggregate TEK-sensor alignment across all member farms for a given month.

    Fields with zero applicable TEK practices for the (month, crop_type) pair
    are NOT counted in `total_fields_assessed` but the farm still appears with
    fields_assessed=0 so reviewers can see the full member roster.
    """
    resolved_month = month if month is not None else date.today().month

    farms_detail: list[dict] = []
    all_alignments: list[float] = []
    support_counter: Counter = Counter()

    for farm in cooperative.farms:
        fields = db.query(Field).filter(Field.farm_id == farm.id).all()
        farm_alignments: list[float] = []

        for field in fields:
            result = compute_tek_alignment(field, resolved_month, db)
            practices = result.get("practices", [])
            if not practices:
                continue  # no applicable practices for this field/month/crop
            farm_alignments.append(float(result["alignment_score_pct"]))
            for p in practices:
                if p.get("sensor_support"):
                    support_counter[p["name"]] += 1

        avg_farm = (
            round(sum(farm_alignments) / len(farm_alignments), 1)
            if farm_alignments
            else 0.0
        )
        farms_detail.append({
            "farm_id": farm.id,
            "farm_name": farm.name,
            "avg_alignment_pct": avg_farm,
            "fields_assessed": len(farm_alignments),
        })
        all_alignments.extend(farm_alignments)

    overall = (
        round(sum(all_alignments) / len(all_alignments), 1)
        if all_alignments
        else 0.0
    )
    top_practice = support_counter.most_common(1)[0][0] if support_counter else None

    return {
        "cooperative_id": cooperative.id,
        "month": resolved_month,
        "overall_adoption_pct": overall,
        "top_practice_es": top_practice,
        "total_fields_assessed": len(all_alignments),
        "farms": farms_detail,
    }
