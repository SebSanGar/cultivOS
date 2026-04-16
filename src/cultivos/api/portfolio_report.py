"""Multi-farm portfolio PDF report endpoint."""

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.models import (
    Farm, Field, HealthScore, SoilAnalysis, TreatmentRecord,
)
from cultivos.db.session import get_db
from cultivos.services.reports import generate_portfolio_report_pdf

router = APIRouter(prefix="/api/reports", tags=["reports"], dependencies=[Depends(get_current_user)])


@router.post("/portfolio")
def generate_portfolio_report(db: Session = Depends(get_db)):
    """Generate a multi-farm portfolio PDF summarising health, carbon, and economics."""
    farms = db.query(Farm).all()

    farm_details = []
    total_fields = 0
    total_hectares = 0.0
    all_health_scores = []

    for farm in farms:
        fields = db.query(Field).filter(Field.farm_id == farm.id).all()
        field_ids = [f.id for f in fields]
        ha = sum(f.hectares or 0 for f in fields)
        total_hectares += ha
        total_fields += len(fields)

        # Per-farm avg health
        health_scores = []
        dominant_trend = "stable"
        for fid in field_ids:
            latest = (
                db.query(HealthScore)
                .filter(HealthScore.field_id == fid)
                .order_by(HealthScore.scored_at.desc())
                .first()
            )
            if latest:
                health_scores.append(float(latest.score))
                dominant_trend = latest.trend or dominant_trend

        avg_health = sum(health_scores) / len(health_scores) if health_scores else 0.0
        all_health_scores.extend(health_scores)

        treatment_count = (
            db.query(func.count(TreatmentRecord.id))
            .filter(TreatmentRecord.field_id.in_(field_ids))
            .scalar()
        ) if field_ids else 0
        treatment_count = treatment_count or 0

        farm_details.append({
            "name": farm.name,
            "municipality": farm.municipality,
            "state": farm.state,
            "hectares": ha,
            "avg_health": avg_health,
            "health_trend": dominant_trend,
            "field_count": len(fields),
            "treatment_count": treatment_count,
        })

    portfolio_avg_health = (
        sum(all_health_scores) / len(all_health_scores) if all_health_scores else 0.0
    )

    farms_summary = {
        "total_farms": len(farms),
        "total_hectares": total_hectares,
        "avg_health_score": portfolio_avg_health,
        "total_fields": total_fields,
    }

    # Carbon summary — aggregate from soil data
    from cultivos.services.intelligence.carbon import estimate_soc
    _SOC_TO_CO2E = 3.67

    soil_fields = (
        db.query(Field)
        .join(SoilAnalysis, SoilAnalysis.field_id == Field.id)
        .filter(SoilAnalysis.organic_matter_pct.isnot(None))
        .distinct()
        .all()
    )
    total_co2e = 0.0
    total_soc = 0.0
    soc_count = 0
    for field in soil_fields:
        latest_soil = (
            db.query(SoilAnalysis)
            .filter(SoilAnalysis.field_id == field.id, SoilAnalysis.organic_matter_pct.isnot(None))
            .order_by(SoilAnalysis.sampled_at.desc())
            .first()
        )
        if latest_soil:
            soc = estimate_soc(
                organic_matter_pct=float(latest_soil.organic_matter_pct),
                depth_cm=float(latest_soil.depth_cm or 30.0),
            )
            ha = float(field.hectares or 0)
            soc_per_ha = soc["soc_tonnes_per_ha"]
            total_co2e += soc_per_ha * ha * _SOC_TO_CO2E
            total_soc += soc_per_ha
            soc_count += 1

    carbon_summary = {
        "total_co2e_tonnes": round(total_co2e, 1),
        "avg_soc_tonnes_per_ha": round(total_soc / soc_count, 1) if soc_count else 0,
    }

    # Economic summary — reuse existing function
    from cultivos.services.intelligence.economics import calculate_farm_savings

    agg_water = 0
    agg_fert = 0
    agg_yield = 0
    for fd in farm_details:
        result = calculate_farm_savings(
            health_score=fd["avg_health"],
            hectares=fd["hectares"],
            treatment_count=fd["treatment_count"],
            irrigation_efficiency=None,
        )
        agg_water += result["water_savings_mxn"]
        agg_fert += result["fertilizer_savings_mxn"]
        agg_yield += result["yield_improvement_mxn"]

    economic_summary = {
        "total_savings_mxn": agg_water + agg_fert + agg_yield,
        "water_savings_mxn": agg_water,
        "fertilizer_savings_mxn": agg_fert,
        "yield_improvement_mxn": agg_yield,
    }

    pdf_bytes = generate_portfolio_report_pdf(
        farms_summary=farms_summary,
        farm_details=farm_details,
        carbon_summary=carbon_summary,
        economic_summary=economic_summary,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="reporte_portafolio.pdf"',
        },
    )
