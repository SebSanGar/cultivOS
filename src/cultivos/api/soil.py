"""Soil Analysis CRUD endpoints — nested under /api/farms/{farm_id}/fields/{field_id}/soil."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, SoilAnalysis
from cultivos.db.session import get_db
from cultivos.models.soil import SoilAnalysisCreate, SoilAnalysisUpdate, SoilAnalysisOut

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}/soil",
    tags=["soil"],
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


@router.post("", response_model=SoilAnalysisOut, status_code=201)
def create_soil_analysis(
    farm_id: int,
    field_id: int,
    body: SoilAnalysisCreate,
    db: Session = Depends(get_db),
):
    _get_field(farm_id, field_id, db)
    analysis = SoilAnalysis(field_id=field_id, **body.model_dump())
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


@router.get("", response_model=list[SoilAnalysisOut])
def list_soil_analyses(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    _get_field(farm_id, field_id, db)
    return (
        db.query(SoilAnalysis)
        .filter(SoilAnalysis.field_id == field_id)
        .order_by(SoilAnalysis.sampled_at.desc())
        .all()
    )


@router.get("/{soil_id}", response_model=SoilAnalysisOut)
def get_soil_analysis(
    farm_id: int,
    field_id: int,
    soil_id: int,
    db: Session = Depends(get_db),
):
    _get_field(farm_id, field_id, db)
    analysis = (
        db.query(SoilAnalysis)
        .filter(SoilAnalysis.id == soil_id, SoilAnalysis.field_id == field_id)
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Soil analysis not found")
    return analysis


@router.put("/{soil_id}", response_model=SoilAnalysisOut)
def update_soil_analysis(
    farm_id: int,
    field_id: int,
    soil_id: int,
    body: SoilAnalysisUpdate,
    db: Session = Depends(get_db),
):
    _get_field(farm_id, field_id, db)
    analysis = (
        db.query(SoilAnalysis)
        .filter(SoilAnalysis.id == soil_id, SoilAnalysis.field_id == field_id)
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Soil analysis not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(analysis, key, value)
    db.commit()
    db.refresh(analysis)
    return analysis
