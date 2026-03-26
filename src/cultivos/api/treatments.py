"""Treatment recommendation endpoints — nested under /api/farms/{farm_id}/fields/{field_id}/treatments."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, HealthScore, SoilAnalysis, TreatmentRecord
from cultivos.db.session import get_db
from cultivos.models.treatment import TreatmentOut
from cultivos.services.intelligence.recommendations import SoilInput, recommend_treatment

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}/treatments",
    tags=["treatments"],
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


@router.post("", response_model=list[TreatmentOut], status_code=201)
def generate_treatments(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    """Generate treatment recommendations from latest health score and soil data.

    Fetches the most recent health score and soil analysis, runs the pure
    recommendation engine, and stores the results.
    Returns 422 if no health score exists for the field.
    """
    field = _get_field(farm_id, field_id, db)

    # Fetch latest health score
    latest_health = (
        db.query(HealthScore)
        .filter(HealthScore.field_id == field_id)
        .order_by(HealthScore.scored_at.desc())
        .first()
    )
    if not latest_health:
        raise HTTPException(
            status_code=422,
            detail="No health score available for this field. Compute health first.",
        )

    # Fetch latest soil analysis
    latest_soil = (
        db.query(SoilAnalysis)
        .filter(SoilAnalysis.field_id == field_id)
        .order_by(SoilAnalysis.sampled_at.desc())
        .first()
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

    recommendations = recommend_treatment(
        health_score=latest_health.score,
        soil=soil_input,
        crop_type=field.crop_type,
    )

    records = []
    for rec in recommendations:
        record = TreatmentRecord(
            field_id=field_id,
            health_score_used=latest_health.score,
            problema=rec["problema"],
            causa_probable=rec["causa_probable"],
            tratamiento=rec["tratamiento"],
            costo_estimado_mxn=rec["costo_estimado_mxn"],
            urgencia=rec["urgencia"],
            prevencion=rec["prevencion"],
            organic=rec["organic"],
        )
        db.add(record)
        records.append(record)

    db.commit()
    for r in records:
        db.refresh(r)

    return records


@router.get("", response_model=list[TreatmentOut])
def list_treatments(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    """List all treatment records for this field, most recent first."""
    _get_field(farm_id, field_id, db)
    return (
        db.query(TreatmentRecord)
        .filter(TreatmentRecord.field_id == field_id)
        .order_by(TreatmentRecord.created_at.desc())
        .all()
    )
