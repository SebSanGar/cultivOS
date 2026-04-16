"""Economic impact endpoints — farm-level savings estimates."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord
from cultivos.db.session import get_db
from cultivos.models.economics import EconomicImpactOut
from cultivos.services.intelligence.economics import calculate_farm_savings

router = APIRouter(
    prefix="/api/farms/{farm_id}/economic-impact",
    tags=["economics"],
    dependencies=[Depends(get_current_user)]
)


@router.get("", response_model=EconomicImpactOut)
def get_economic_impact(
    farm_id: int,
    db: Session = Depends(get_db),
):
    """Estimate annual economic impact of precision agriculture for a farm."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    # Aggregate data across all fields
    fields = db.query(Field).filter(Field.farm_id == farm_id).all()

    if not fields:
        return EconomicImpactOut(
            farm_id=farm_id,
            hectares=0,
            water_savings_mxn=0,
            fertilizer_savings_mxn=0,
            yield_improvement_mxn=0,
            total_savings_mxn=0,
            nota="Sin parcelas registradas — agregue parcelas para estimar impacto economico.",
        )

    total_hectares = sum(f.hectares or 0 for f in fields)
    field_ids = [f.id for f in fields]

    # Average health score across latest score per field
    health_scores = []
    for fid in field_ids:
        latest = (
            db.query(HealthScore)
            .filter(HealthScore.field_id == fid)
            .order_by(HealthScore.scored_at.desc())
            .first()
        )
        if latest:
            health_scores.append(float(latest.score))

    avg_health = sum(health_scores) / len(health_scores) if health_scores else 50.0

    # Count treatments across all fields
    treatment_count = (
        db.query(func.count(TreatmentRecord.id))
        .filter(TreatmentRecord.field_id.in_(field_ids))
        .scalar()
    ) or 0

    result = calculate_farm_savings(
        health_score=avg_health,
        hectares=total_hectares,
        treatment_count=treatment_count,
        irrigation_efficiency=None,  # no irrigation sensor data yet
    )

    return EconomicImpactOut(
        farm_id=farm_id,
        hectares=total_hectares,
        water_savings_mxn=result["water_savings_mxn"],
        fertilizer_savings_mxn=result["fertilizer_savings_mxn"],
        yield_improvement_mxn=result["yield_improvement_mxn"],
        total_savings_mxn=result["total_savings_mxn"],
        nota=result["nota"],
    )
