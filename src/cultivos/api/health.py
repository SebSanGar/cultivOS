"""Health scoring endpoints — nested under /api/farms/{farm_id}/fields/{field_id}/health."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, HealthScore, MicrobiomeRecord, NDVIResult, SoilAnalysis, ThermalResult
from cultivos.db.session import get_db
from cultivos.models.health import HealthHistoryOut, HealthScoreOut
from cultivos.services.crop.health import MicrobiomeInput, NDVIInput, SoilInput, ThermalInput, compute_health_score, compute_trend_from_history

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}/health",
    tags=["health"],
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


@router.post("", response_model=HealthScoreOut, status_code=201)
def compute_field_health(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    """Compute health score from latest NDVI and soil data for this field.

    Automatically fetches the most recent NDVI result and soil analysis.
    Returns a partial score if only one data source is available.
    Returns 422 if neither NDVI nor soil data exists for the field.
    """
    _get_field(farm_id, field_id, db)

    # Fetch latest NDVI result
    latest_ndvi = (
        db.query(NDVIResult)
        .filter(NDVIResult.field_id == field_id)
        .order_by(NDVIResult.analyzed_at.desc())
        .first()
    )

    # Fetch latest soil analysis
    latest_soil = (
        db.query(SoilAnalysis)
        .filter(SoilAnalysis.field_id == field_id)
        .order_by(SoilAnalysis.sampled_at.desc())
        .first()
    )

    # Fetch latest microbiome record
    latest_microbiome = (
        db.query(MicrobiomeRecord)
        .filter(MicrobiomeRecord.field_id == field_id)
        .order_by(MicrobiomeRecord.sampled_at.desc())
        .first()
    )

    # Fetch latest thermal result
    latest_thermal = (
        db.query(ThermalResult)
        .filter(ThermalResult.field_id == field_id)
        .order_by(ThermalResult.analyzed_at.desc())
        .first()
    )

    if not latest_ndvi and not latest_soil and not latest_microbiome and not latest_thermal:
        raise HTTPException(
            status_code=422,
            detail="No NDVI, soil, microbiome, or thermal data available for this field. Submit at least one before computing health.",
        )

    # Build inputs
    ndvi_input: NDVIInput | None = None
    if latest_ndvi:
        ndvi_input = NDVIInput(
            ndvi_mean=latest_ndvi.ndvi_mean,
            ndvi_std=latest_ndvi.ndvi_std,
            stress_pct=latest_ndvi.stress_pct,
        )

    soil_input: SoilInput | None = None
    if latest_soil:
        soil_input = SoilInput(
            ph=latest_soil.ph,
            organic_matter_pct=latest_soil.organic_matter_pct,
            nitrogen_ppm=latest_soil.nitrogen_ppm,
            phosphorus_ppm=latest_soil.phosphorus_ppm,
            potassium_ppm=latest_soil.potassium_ppm,
            moisture_pct=latest_soil.moisture_pct,
        )

    microbiome_input: MicrobiomeInput | None = None
    if latest_microbiome:
        microbiome_input = MicrobiomeInput(
            respiration_rate=latest_microbiome.respiration_rate,
            microbial_biomass_carbon=latest_microbiome.microbial_biomass_carbon,
            fungi_bacteria_ratio=latest_microbiome.fungi_bacteria_ratio,
            classification=latest_microbiome.classification,
        )

    thermal_input: ThermalInput | None = None
    if latest_thermal:
        thermal_input = ThermalInput(
            stress_pct=latest_thermal.stress_pct,
            temp_mean=latest_thermal.temp_mean,
            irrigation_deficit=latest_thermal.irrigation_deficit,
        )

    # Get previous score for trend
    previous = (
        db.query(HealthScore)
        .filter(HealthScore.field_id == field_id)
        .order_by(HealthScore.scored_at.desc())
        .first()
    )
    previous_score = previous.score if previous else None

    result = compute_health_score(
        ndvi=ndvi_input,
        soil=soil_input,
        previous_score=previous_score,
        microbiome=microbiome_input,
        thermal=thermal_input,
    )

    record = HealthScore(
        field_id=field_id,
        score=result["score"],
        ndvi_mean=latest_ndvi.ndvi_mean if latest_ndvi else None,
        ndvi_std=latest_ndvi.ndvi_std if latest_ndvi else None,
        stress_pct=latest_ndvi.stress_pct if latest_ndvi else None,
        soil_ph=latest_soil.ph if latest_soil else None,
        soil_organic_matter_pct=latest_soil.organic_matter_pct if latest_soil else None,
        trend=result["trend"],
        sources=result["sources"],
        breakdown=result["breakdown"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=list[HealthScoreOut])
def list_health_scores(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    """List all health scores for this field, most recent first."""
    _get_field(farm_id, field_id, db)
    return (
        db.query(HealthScore)
        .filter(HealthScore.field_id == field_id)
        .order_by(HealthScore.scored_at.desc())
        .all()
    )


@router.get("/history", response_model=HealthHistoryOut)
def get_health_history(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    """Get chronological health score history with computed overall trend.

    Returns all health scores for this field ordered oldest-first,
    plus a computed trend from the score values (requires 3+ scores).
    """
    _get_field(farm_id, field_id, db)
    records = (
        db.query(HealthScore)
        .filter(HealthScore.field_id == field_id)
        .order_by(HealthScore.scored_at.asc())
        .all()
    )
    score_values = [r.score for r in records]
    trend = compute_trend_from_history(score_values)
    return HealthHistoryOut(
        scores=[HealthScoreOut.model_validate(r) for r in records],
        trend=trend,
        count=len(records),
    )


@router.get("/{score_id}", response_model=HealthScoreOut)
def get_health_score(
    farm_id: int,
    field_id: int,
    score_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific health score by ID."""
    _get_field(farm_id, field_id, db)
    score = (
        db.query(HealthScore)
        .filter(HealthScore.id == score_id, HealthScore.field_id == field_id)
        .first()
    )
    if not score:
        raise HTTPException(status_code=404, detail="Health score not found")
    return score
