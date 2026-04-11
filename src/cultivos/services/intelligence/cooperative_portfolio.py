"""Cooperative portfolio health service.

Aggregates health, carbon, and economic metrics across all farms in a cooperative.
"""

from __future__ import annotations

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from cultivos.db.models import (
    CarbonBaseline,
    Cooperative,
    Farm,
    Field,
    HealthScore,
    TreatmentRecord,
)
from cultivos.services.intelligence.carbon import compute_carbon_projection
from cultivos.services.intelligence.economics import calculate_farm_savings

# Threshold below which a field is "needing attention"
ATTENTION_THRESHOLD = 40.0


def compute_portfolio_health(coop: Cooperative, db: Session) -> dict:
    """Aggregate portfolio health metrics for a cooperative.

    Returns dict with:
        cooperative_id, name, total_farms, total_fields, total_hectares,
        avg_health_score, fields_needing_attention, total_co2e_sequestered,
        economic_impact_mxn
    """
    farms = db.query(Farm).filter(Farm.cooperative_id == coop.id).all()

    if not farms:
        return {
            "cooperative_id": coop.id,
            "name": coop.name,
            "total_farms": 0,
            "total_fields": 0,
            "total_hectares": 0.0,
            "avg_health_score": None,
            "fields_needing_attention": 0,
            "total_co2e_sequestered": 0.0,
            "economic_impact_mxn": 0,
        }

    farm_ids = [f.id for f in farms]
    total_hectares = sum(f.total_hectares or 0.0 for f in farms)

    fields = db.query(Field).filter(Field.farm_id.in_(farm_ids)).all()
    total_fields = len(fields)
    field_ids = [f.id for f in fields]

    # ── Latest health score per field ─────────────────────────────────────────
    field_health: dict[int, float] = {}
    if field_ids:
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
        field_health = {hs.field_id: hs.score for hs in latest_scores}

    all_scores = list(field_health.values())
    avg_health_score = round(sum(all_scores) / len(all_scores), 1) if all_scores else None
    fields_needing_attention = sum(1 for s in all_scores if s < ATTENTION_THRESHOLD)

    # ── Carbon: sum current_co2e_t from latest baseline per field ─────────────
    total_co2e = 0.0
    if field_ids:
        # Get latest baseline per field
        latest_cb_sub = (
            db.query(
                CarbonBaseline.field_id,
                func.max(CarbonBaseline.recorded_at).label("max_recorded"),
            )
            .filter(CarbonBaseline.field_id.in_(field_ids))
            .group_by(CarbonBaseline.field_id)
            .subquery()
        )
        latest_baselines = (
            db.query(CarbonBaseline)
            .join(
                latest_cb_sub,
                and_(
                    CarbonBaseline.field_id == latest_cb_sub.c.field_id,
                    CarbonBaseline.recorded_at == latest_cb_sub.c.max_recorded,
                ),
            )
            .all()
        )
        # Map field_id → hectares for projection
        field_hectares = {f.id: (f.hectares or 0.0) for f in fields}
        for cb in latest_baselines:
            h = field_hectares.get(cb.field_id, 0.0)
            if h > 0:
                proj = compute_carbon_projection(cb.soc_percent, h, cb.lab_method)
                total_co2e += proj["current_co2e_t"]

    # ── Economic impact: sum per farm ─────────────────────────────────────────
    total_economic = 0
    farm_fields_map: dict[int, list[Field]] = {}
    for f in fields:
        farm_fields_map.setdefault(f.farm_id, []).append(f)

    for farm in farms:
        ff = farm_fields_map.get(farm.id, [])
        ff_ids = [f.id for f in ff]
        farm_health_vals = [field_health[fid] for fid in ff_ids if fid in field_health]
        avg_farm_health = sum(farm_health_vals) / len(farm_health_vals) if farm_health_vals else 50.0
        treatment_count = (
            db.query(func.count(TreatmentRecord.id))
            .filter(TreatmentRecord.field_id.in_(ff_ids))
            .scalar() or 0
        ) if ff_ids else 0
        result = calculate_farm_savings(
            health_score=avg_farm_health,
            hectares=farm.total_hectares or 0.0,
            treatment_count=treatment_count,
            irrigation_efficiency=None,
        )
        total_economic += result["total_savings_mxn"]

    return {
        "cooperative_id": coop.id,
        "name": coop.name,
        "total_farms": len(farms),
        "total_fields": total_fields,
        "total_hectares": total_hectares,
        "avg_health_score": avg_health_score,
        "fields_needing_attention": fields_needing_attention,
        "total_co2e_sequestered": round(total_co2e, 2),
        "economic_impact_mxn": total_economic,
    }
