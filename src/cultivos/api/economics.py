"""Economic impact endpoints — farm-level savings estimates."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord
from cultivos.db.session import get_db
from cultivos.models.economics import EconomicImpactOut
from cultivos.services.intelligence.assumptions import get_value as _a
from cultivos.services.intelligence.economics import calculate_farm_savings

_TIER_RATES = {
    "basic": _a("tier_rate_basic_mxn_ha"),
    "standard": _a("tier_rate_standard_mxn_ha"),
}

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

_CONFIDENCE_LABELS = {
    "low": "Estimado",
    "medium": "Medido",
    "high": "Confirmado",
}

_NO_DATA_OUT = dict(
    hectares=0,
    water_savings_mxn=0,
    fertilizer_savings_mxn=0,
    yield_improvement_mxn=0,
    total_savings_mxn=0,
    total_savings_low_mxn=0,
    total_savings_high_mxn=0,
    confidence="low",
    confidence_label="Estimado",
    is_estimate=True,
    basis=_BASIS,
    subscription_cost_mxn=None,
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

    # Total health score rows across all fields (for confidence tier, not avg_health)
    total_score_count = (
        db.query(func.count(HealthScore.id))
        .filter(HealthScore.field_id.in_(field_ids))
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

    # Confidence based on total data volume across all fields
    if total_score_count >= 6 and treatment_count >= 6:
        confidence = "high"
    elif total_score_count >= 3 and treatment_count >= 3:
        confidence = "medium"
    else:
        confidence = "low"
    confidence_label = _CONFIDENCE_LABELS[confidence]

    nota = result["nota"]
    # Drop causal language; replace with honest qualifier
    nota = nota.replace(
        "La agricultura de precision esta generando valor real.",
        "Estimacion basada en tus datos actuales; el valor real depende de la temporada.",
    )

    # Subscription cost from tier
    tier = getattr(farm, "tier", None)
    if tier and tier in _TIER_RATES:
        subscription_cost_mxn: int | None = round(total_hectares * _TIER_RATES[tier])
    else:
        subscription_cost_mxn = None
        nota = nota + " Tarifa no configurada para esta granja."

    # Net ROI — only when we have real data AND a subscription cost
    has_real_data = len(health_scores) >= 1 and treatment_count >= 1
    if subscription_cost_mxn is not None and has_real_data and subscription_cost_mxn > 0:
        net_savings_mxn: int | None = total - subscription_cost_mxn
        roi_multiple: float | None = round(total / subscription_cost_mxn, 1)
        payback_months: int | None = round(12 / roi_multiple) if roi_multiple > 0 else None
    else:
        net_savings_mxn = None
        roi_multiple = None
        payback_months = None

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
        confidence_label=confidence_label,
        is_estimate=True,
        basis=_BASIS,
        subscription_cost_mxn=subscription_cost_mxn,
        net_savings_mxn=net_savings_mxn,
        roi_multiple=roi_multiple,
        payback_months=payback_months,
        nota=nota,
    )
