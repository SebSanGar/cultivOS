"""Economic impact endpoints — farm-level savings estimates."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord
from cultivos.db.session import get_db
from cultivos.models.economics import EconomicImpactOut
from cultivos.services.intelligence.economics import calculate_farm_savings

router = APIRouter(
    prefix="/api/farms/{farm_id}/economic-impact",
    tags=["economics"],
)

_BASIS = [
    "water_savings_per_ha",
    "fertilizer_savings_per_ha",
    "yield_baseline_per_ha",
    "default_irrigation_efficiency",
]

_NO_DATA_OUT = dict(
    hectares=0,
    water_savings_mxn=0,
    fertilizer_savings_mxn=0,
    yield_improvement_mxn=0,
    total_savings_mxn=0,
    total_savings_low_mxn=0,
    total_savings_high_mxn=0,
    confidence="low",
    is_estimate=True,
    basis=_BASIS,
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

    fields = db.query(Field).filter(Field.farm_id == farm_id).all()

    if not fields:
        return EconomicImpactOut(
            farm_id=farm_id,
            nota="Sin parcelas registradas — agregue parcelas para estimar impacto economico.",
            **_NO_DATA_OUT,
        )

    total_hectares = sum(f.hectares or 0 for f in fields)
    field_ids = [f.id for f in fields]

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

    treatment_count = (
        db.query(func.count(TreatmentRecord.id))
        .filter(TreatmentRecord.field_id.in_(field_ids))
        .scalar()
    ) or 0

    result = calculate_farm_savings(
        health_score=avg_health,
        hectares=total_hectares,
        treatment_count=treatment_count,
        irrigation_efficiency=None,
    )

    total = result["total_savings_mxn"]
    low = round(total * 0.6)
    high = total  # current estimate is the 1.0× upper bound

    # Confidence based on data availability
    if len(health_scores) >= 3 and treatment_count >= 3:
        confidence = "medium"
    elif len(health_scores) >= 1:
        confidence = "low"
    else:
        confidence = "low"

    nota = result["nota"]
    # Drop causal language; replace with honest qualifier
    nota = nota.replace(
        "La agricultura de precision esta generando valor real.",
        "Estimacion basada en tus datos actuales; el valor real depende de la temporada.",
    )

    return EconomicImpactOut(
        farm_id=farm_id,
        hectares=total_hectares,
        water_savings_mxn=result["water_savings_mxn"],
        fertilizer_savings_mxn=result["fertilizer_savings_mxn"],
        yield_improvement_mxn=result["yield_improvement_mxn"],
        total_savings_mxn=total,
        total_savings_low_mxn=low,
        total_savings_high_mxn=high,
        confidence=confidence,
        is_estimate=True,
        basis=_BASIS,
        nota=nota,
    )
