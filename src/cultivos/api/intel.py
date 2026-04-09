"""Intelligence dashboard API — cross-farm analytics for admin/research team."""

import csv
import io
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from cultivos.auth import require_role
from cultivos.db.models import Farm, FarmerFeedback, Field, HealthScore, NDVIResult, SoilAnalysis, TreatmentRecord
from cultivos.db.session import get_db
from cultivos.models.feedback import TEKMethodValidation, TEKValidationOut, TreatmentTrustOut
from cultivos.services.intelligence.feedback_aggregation import aggregate_treatment_trust
from cultivos.models.intel import (
    AnomaliesOut,
    BatchHealthOut,
    BatchHealthRequestIn,
    FarmCompareOut,
    IntelCarbonSummaryOut,
    IntelEconomicsOut,
    IntelSummaryOut,
    RegionalSummaryOut,
    SeasonalOut,
    SensorFusionOverviewOut,
    SoilTrendsOut,
    TimingOut,
    TimingRequestIn,
    TreatmentEffectivenessOut,
    TreatmentEffectivenessReportOut,
    CerebroAnalyticsOut,
    PredictionAccuracyOut,
    ExecutiveSummaryOut,
)
from cultivos.services.intelligence.analytics import (
    compare_farms,
    compute_anomalies,
    compute_batch_health,
    compute_carbon_summary,
    compute_cerebro_analytics,
    compute_prediction_accuracy,
    compute_economics_summary,
    compute_regional_summary,
    compute_seasonal_performance,
    compute_sensor_fusion_overview,
    compute_soil_trends,
    compute_summary,
    compute_treatment_effectiveness,
    compute_treatment_effectiveness_report,
    compute_executive_summary,
)
from cultivos.services.intelligence.recommendations import optimize_treatment_timing

router = APIRouter(prefix="/api/intel", tags=["intelligence"])

_admin_or_researcher = require_role("admin", "researcher")


@router.get("/cerebro-analytics", response_model=CerebroAnalyticsOut)
def intel_cerebro_analytics(
    db: Session = Depends(get_db),
):
    """Cerebro AI decision log and analytics — aggregate AI activity counts, accuracy, trends."""
    result = compute_cerebro_analytics(db)
    return CerebroAnalyticsOut(**result)


@router.get("/prediction-accuracy", response_model=PredictionAccuracyOut)
def intel_prediction_accuracy(
    db: Session = Depends(get_db),
):
    """Prediction accuracy tracker — compare AI forecasts vs actual outcomes."""
    result = compute_prediction_accuracy(db)
    return PredictionAccuracyOut(**result)


@router.get("/executive-summary", response_model=ExecutiveSummaryOut)
def intel_executive_summary(
    db: Session = Depends(get_db),
):
    """Platform-wide executive KPIs — total farms, fields, health, CO2e, treatments, alerts."""
    result = compute_executive_summary(db)
    return ExecutiveSummaryOut(**result)


@router.get("/compare", response_model=FarmCompareOut)
def intel_compare(
    farm_ids: str,
    db: Session = Depends(get_db),
    user=Depends(_admin_or_researcher),
):
    """Compare health, yield, and treatments across selected farms."""
    try:
        ids = [int(x.strip()) for x in farm_ids.split(",")]
    except ValueError:
        raise HTTPException(status_code=422, detail="farm_ids must be comma-separated integers")
    try:
        return compare_farms(db, ids)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/summary", response_model=IntelSummaryOut)
def intel_summary(
    db: Session = Depends(get_db),
    user=Depends(_admin_or_researcher),
):
    """Return a high-level intelligence summary across all farms, including health stats and alert counts."""
    return compute_summary(db)


@router.get("/economics", response_model=IntelEconomicsOut)
def intel_economics(
    db: Session = Depends(get_db),
    user=Depends(_admin_or_researcher),
):
    """Aggregate economic impact across all farms — total and per-farm savings in MXN."""
    return compute_economics_summary(db)


@router.get("/carbon", response_model=IntelCarbonSummaryOut)
def intel_carbon(
    db: Session = Depends(get_db),
    user=Depends(_admin_or_researcher),
):
    """Aggregate carbon sequestration metrics across all fields — SOC, CO2e, trend per field."""
    return compute_carbon_summary(db)


@router.get("/sensor-fusion", response_model=SensorFusionOverviewOut)
def intel_sensor_fusion(
    db: Session = Depends(get_db),
    user=Depends(_admin_or_researcher),
):
    """Cross-field sensor fusion validation — confidence scores and contradiction flags per field."""
    return compute_sensor_fusion_overview(db)


@router.get("/soil-trends", response_model=SoilTrendsOut)
def intel_soil_trends(
    db: Session = Depends(get_db),
    user=Depends(_admin_or_researcher),
):
    """Return soil health trends aggregated across all fields over time."""
    return compute_soil_trends(db)


@router.get("/treatments", response_model=TreatmentEffectivenessOut)
def intel_treatments(
    db: Session = Depends(get_db),
    user=Depends(_admin_or_researcher),
):
    """Return treatment effectiveness metrics showing which treatments improve crop health."""
    return compute_treatment_effectiveness(db)


@router.get("/treatment-effectiveness-report", response_model=TreatmentEffectivenessReportOut)
def intel_treatment_effectiveness_report(
    crop_type: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(_admin_or_researcher),
):
    """Aggregate treatment effectiveness ranked by composite score."""
    return compute_treatment_effectiveness_report(db, crop_type=crop_type)


@router.get("/anomalies", response_model=AnomaliesOut)
def intel_anomalies(
    db: Session = Depends(get_db),
    user=Depends(_admin_or_researcher),
):
    """Detect and return fields with anomalous health scores or unusual trend changes."""
    return compute_anomalies(db)


@router.get("/regional-summary", response_model=RegionalSummaryOut)
def intel_regional_summary(
    state: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(_admin_or_researcher),
):
    """Aggregate intelligence across all farms in a region — crop performance, treatment success, seasonal patterns."""
    return compute_regional_summary(db, state=state)


@router.get("/treatment-trust", response_model=TreatmentTrustOut)
def treatment_trust(
    crop_type: Optional[str] = None,
    field_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user=Depends(_admin_or_researcher),
):
    """Aggregate farmer feedback into per-treatment trust scores ranked by farmer confidence."""
    items = aggregate_treatment_trust(db, crop_type=crop_type, field_id=field_id)
    return TreatmentTrustOut(treatments=[item for item in items])


@router.get("/tek-validation", response_model=TEKValidationOut)
def tek_validation(
    db: Session = Depends(get_db),
    user=Depends(_admin_or_researcher),
):
    """Aggregate farmer feedback by ancestral method to see which ancestral methods farmers trust."""
    # Get all feedback joined with treatments that have an ancestral method
    results = (
        db.query(FarmerFeedback, TreatmentRecord)
        .join(TreatmentRecord, FarmerFeedback.treatment_id == TreatmentRecord.id)
        .filter(TreatmentRecord.ancestral_method_name.isnot(None))
        .all()
    )

    # Aggregate by method name
    method_data: dict[str, list[FarmerFeedback]] = {}
    for feedback, treatment in results:
        name = treatment.ancestral_method_name
        method_data.setdefault(name, []).append(feedback)

    methods = []
    for method_name, feedbacks in method_data.items():
        total = len(feedbacks)
        positive = sum(1 for f in feedbacks if f.worked)
        negative = total - positive
        avg_rating = sum(f.rating for f in feedbacks) / total
        # Trust score: weighted combination of positive ratio (60%) and normalized rating (40%)
        positive_ratio = positive / total if total > 0 else 0
        rating_normalized = (avg_rating - 1) / 4  # 1-5 → 0-1
        trust_score = round((positive_ratio * 0.6 + rating_normalized * 0.4) * 100, 1)

        methods.append(TEKMethodValidation(
            method_name=method_name,
            total_feedback=total,
            positive_count=positive,
            negative_count=negative,
            average_rating=round(avg_rating, 2),
            trust_score=trust_score,
        ))

    # Sort by trust score descending
    methods.sort(key=lambda m: m.trust_score, reverse=True)
    return TEKValidationOut(methods=methods)


@router.post("/treatment-timing", response_model=TimingOut)
def treatment_timing(body: TimingRequestIn):
    """Recommend optimal day and time to apply a treatment based on weather forecast."""
    forecast = [f.model_dump() for f in body.forecast_3day]
    return optimize_treatment_timing(body.treatment_type, forecast)


@router.post("/batch-health", response_model=BatchHealthOut)
def batch_field_health(
    body: BatchHealthRequestIn,
    db: Session = Depends(get_db),
    user=Depends(_admin_or_researcher),
):
    """Compute health score + trend for multiple fields in one call.

    Optimized for dashboard map rendering. Invalid IDs return null entries.
    """
    return compute_batch_health(db, body.field_ids)


_INTEL_CSV_HEADERS = [
    "Granja",
    "Parcela",
    "Cultivo",
    "Hectareas",
    "Salud",
    "Tendencia",
    "NDVI Promedio",
    "pH Suelo",
    "Materia Organica %",
    "Tratamientos",
    "Ultimo Tratamiento",
]

_TREND_MAP = {
    "improving": "Mejorando",
    "stable": "Estable",
    "declining": "Declinando",
}


@router.get("/export")
def intel_export(
    db: Session = Depends(get_db),
    user=Depends(_admin_or_researcher),
):
    """Export all field data across all farms as CSV for researchers and grant reviewers."""
    farms = db.query(Farm).order_by(Farm.name).all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(_INTEL_CSV_HEADERS)

    for farm in farms:
        fields = db.query(Field).filter(Field.farm_id == farm.id).order_by(Field.name).all()
        for field in fields:
            latest_hs = (
                db.query(HealthScore)
                .filter(HealthScore.field_id == field.id)
                .order_by(HealthScore.scored_at.desc())
                .first()
            )
            latest_ndvi = (
                db.query(NDVIResult)
                .filter(NDVIResult.field_id == field.id)
                .order_by(NDVIResult.analyzed_at.desc())
                .first()
            )
            latest_soil = (
                db.query(SoilAnalysis)
                .filter(SoilAnalysis.field_id == field.id)
                .order_by(SoilAnalysis.sampled_at.desc())
                .first()
            )
            treatment_count = (
                db.query(func.count(TreatmentRecord.id))
                .filter(TreatmentRecord.field_id == field.id)
                .scalar()
            )
            last_treatment = (
                db.query(TreatmentRecord)
                .filter(TreatmentRecord.field_id == field.id)
                .order_by(TreatmentRecord.applied_at.desc())
                .first()
            )

            score = latest_hs.score if latest_hs else None
            trend = latest_hs.trend if latest_hs else None
            ndvi = latest_ndvi.ndvi_mean if latest_ndvi else None
            ph = latest_soil.ph if latest_soil else None
            om = latest_soil.organic_matter_pct if latest_soil else None
            last_date = last_treatment.applied_at if last_treatment and last_treatment.applied_at else None

            writer.writerow([
                farm.name,
                field.name,
                field.crop_type or "",
                field.hectares,
                f"{score:.1f}" if score is not None else "",
                _TREND_MAP.get(trend, trend) if trend else "",
                f"{ndvi:.3f}" if ndvi is not None else "",
                f"{ph:.1f}" if ph is not None else "",
                f"{om:.1f}" if om is not None else "",
                treatment_count,
                last_date.strftime("%Y-%m-%d") if last_date else "",
            ])

    return Response(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="cultivOS_intel_export.csv"',
        },
    )


seasonal_router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}",
    tags=["intelligence"],
)


def _get_field(farm_id: int, field_id: int, db: Session) -> Field:
    """Validate farm and field exist and are linked."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@seasonal_router.get("/seasonal", response_model=SeasonalOut)
def field_seasonal(
    farm_id: int,
    field_id: int,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Return seasonal performance breakdown for a field, optionally filtered by year."""
    field = _get_field(farm_id, field_id, db)
    return compute_seasonal_performance(db, field.id, year=year)


@router.get("/data-completeness-global")
def get_global_data_completeness(
    state: Optional[str] = None,
    db: Session = Depends(get_db),
    _user=Depends(require_role("admin")),
):
    """Return data completeness summary across all farms."""
    from cultivos.services.intelligence.completeness import compute_global_data_completeness

    return compute_global_data_completeness(db, state=state)
