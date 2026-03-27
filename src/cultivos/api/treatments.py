"""Treatment recommendation endpoints — nested under /api/farms/{farm_id}/fields/{field_id}/treatments."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, HealthScore, MicrobiomeRecord, SoilAnalysis, TreatmentRecord
from cultivos.db.session import get_db
from cultivos.models.treatment import (
    TreatmentAppliedIn,
    TreatmentEffectivenessOut,
    TreatmentOut,
    TreatmentTimelineEntry,
)
from cultivos.services.intelligence.recommendations import MicrobiomeInput, SoilInput, recommend_treatment

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

    # Fetch latest microbiome record
    latest_microbiome = (
        db.query(MicrobiomeRecord)
        .filter(MicrobiomeRecord.field_id == field_id)
        .order_by(MicrobiomeRecord.sampled_at.desc())
        .first()
    )
    microbiome_input: MicrobiomeInput | None = None
    if latest_microbiome:
        microbiome_input = MicrobiomeInput(
            respiration_rate=latest_microbiome.respiration_rate,
            microbial_biomass_carbon=latest_microbiome.microbial_biomass_carbon,
            fungi_bacteria_ratio=latest_microbiome.fungi_bacteria_ratio,
            classification=latest_microbiome.classification,
        )

    recommendations = recommend_treatment(
        health_score=latest_health.score,
        soil=soil_input,
        crop_type=field.crop_type,
        microbiome=microbiome_input,
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


@router.get("/treatment-history", response_model=list[TreatmentTimelineEntry])
def treatment_history(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    """Chronological timeline of applied treatments for this field."""
    _get_field(farm_id, field_id, db)
    records = (
        db.query(TreatmentRecord)
        .filter(TreatmentRecord.field_id == field_id, TreatmentRecord.applied_at.isnot(None))
        .order_by(TreatmentRecord.applied_at.asc())
        .all()
    )
    return [
        TreatmentTimelineEntry(
            treatment_id=r.id,
            problema=r.problema,
            tratamiento=r.tratamiento,
            urgencia=r.urgencia,
            applied_at=r.applied_at,
            applied_notes=r.applied_notes,
            health_score_used=r.health_score_used,
            created_at=r.created_at,
        )
        for r in records
    ]


@router.get("/{treatment_id}/effectiveness", response_model=TreatmentEffectivenessOut)
def treatment_effectiveness(
    farm_id: int,
    field_id: int,
    treatment_id: int,
    db: Session = Depends(get_db),
):
    """Measure treatment effectiveness by comparing health scores before/after application."""
    _get_field(farm_id, field_id, db)
    record = db.query(TreatmentRecord).filter(
        TreatmentRecord.id == treatment_id,
        TreatmentRecord.field_id == field_id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Treatment not found")

    if not record.applied_at:
        return TreatmentEffectivenessOut(
            treatment_id=record.id,
            problema=record.problema,
            tratamiento=record.tratamiento,
            applied_at=None,
            score_before=None,
            score_after=None,
            delta=None,
            status="not_applied",
        )

    # Find closest health score BEFORE application
    score_before_rec = (
        db.query(HealthScore)
        .filter(HealthScore.field_id == field_id, HealthScore.scored_at <= record.applied_at)
        .order_by(HealthScore.scored_at.desc())
        .first()
    )
    # Find closest health score AFTER application
    score_after_rec = (
        db.query(HealthScore)
        .filter(HealthScore.field_id == field_id, HealthScore.scored_at > record.applied_at)
        .order_by(HealthScore.scored_at.asc())
        .first()
    )

    if not score_before_rec or not score_after_rec:
        return TreatmentEffectivenessOut(
            treatment_id=record.id,
            problema=record.problema,
            tratamiento=record.tratamiento,
            applied_at=record.applied_at,
            score_before=score_before_rec.score if score_before_rec else None,
            score_after=score_after_rec.score if score_after_rec else None,
            delta=None,
            status="insufficient_data",
        )

    delta = round(score_after_rec.score - score_before_rec.score, 1)
    if delta > 5:
        status = "effective"
    elif delta < -5:
        status = "ineffective"
    else:
        status = "neutral"

    return TreatmentEffectivenessOut(
        treatment_id=record.id,
        problema=record.problema,
        tratamiento=record.tratamiento,
        applied_at=record.applied_at,
        score_before=score_before_rec.score,
        score_after=score_after_rec.score,
        delta=delta,
        status=status,
    )


@router.post("/{treatment_id}/applied", response_model=TreatmentOut)
def log_treatment_applied(
    farm_id: int,
    field_id: int,
    treatment_id: int,
    payload: TreatmentAppliedIn,
    db: Session = Depends(get_db),
):
    """Record that a treatment was applied by the farmer."""
    _get_field(farm_id, field_id, db)
    record = db.query(TreatmentRecord).filter(
        TreatmentRecord.id == treatment_id,
        TreatmentRecord.field_id == field_id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Treatment not found")

    record.applied_at = payload.applied_at
    record.applied_notes = payload.notes
    db.commit()
    db.refresh(record)
    return record


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
