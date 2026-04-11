"""Farm-level soil carbon audit service.

Aggregates current_co2e_t, projected_5yr_co2e_t, and annual sequestration
across all fields in a farm using the latest CarbonBaseline per field.
"""

from __future__ import annotations

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from cultivos.db.models import CarbonBaseline, Farm, Field
from cultivos.services.intelligence.carbon import compute_carbon_projection


def compute_carbon_audit(farm: Farm, db: Session) -> dict:
    """Aggregate carbon metrics across all fields in a farm.

    Returns dict with:
        farm_id, total_current_co2e_t, total_projected_5yr_co2e_t,
        total_annual_seq_t_per_yr, fields_with_baseline,
        fields_without_baseline, total_fields
    """
    fields = db.query(Field).filter(Field.farm_id == farm.id).all()
    total_fields = len(fields)

    if total_fields == 0:
        return {
            "farm_id": farm.id,
            "total_current_co2e_t": 0.0,
            "total_projected_5yr_co2e_t": 0.0,
            "total_annual_seq_t_per_yr": 0.0,
            "fields_with_baseline": 0,
            "fields_without_baseline": 0,
            "total_fields": 0,
        }

    field_ids = [f.id for f in fields]
    field_hectares = {f.id: (f.hectares or 0.0) for f in fields}

    # Get latest baseline per field
    latest_sub = (
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
            latest_sub,
            and_(
                CarbonBaseline.field_id == latest_sub.c.field_id,
                CarbonBaseline.recorded_at == latest_sub.c.max_recorded,
            ),
        )
        .all()
    )

    fields_with_baseline = len(latest_baselines)
    fields_without_baseline = total_fields - fields_with_baseline

    total_current = 0.0
    total_projected = 0.0
    total_annual = 0.0

    for cb in latest_baselines:
        h = field_hectares.get(cb.field_id, 0.0)
        if h <= 0:
            continue
        proj = compute_carbon_projection(cb.soc_percent, h, cb.lab_method)
        total_current += proj["current_co2e_t"]
        total_projected += proj["projected_5yr_co2e_t"]
        total_annual += proj["sequestration_rate_t_per_yr"]

    return {
        "farm_id": farm.id,
        "total_current_co2e_t": round(total_current, 2),
        "total_projected_5yr_co2e_t": round(total_projected, 2),
        "total_annual_seq_t_per_yr": round(total_annual, 2),
        "fields_with_baseline": fields_with_baseline,
        "fields_without_baseline": fields_without_baseline,
        "total_fields": total_fields,
    }
