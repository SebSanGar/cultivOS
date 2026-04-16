"""Soil microbiome indicator endpoints — nested under /api/farms/{farm_id}/fields/{field_id}/microbiome."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.models import Farm, Field, MicrobiomeRecord
from cultivos.db.session import get_db
from cultivos.models.microbiome import MicrobiomeCreate, MicrobiomeOut, classify_microbiome

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}/microbiome",
    tags=["microbiome"],
    dependencies=[Depends(get_current_user)]
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


@router.post("", response_model=MicrobiomeOut, status_code=201)
def create_microbiome_record(
    farm_id: int,
    field_id: int,
    body: MicrobiomeCreate,
    db: Session = Depends(get_db),
):
    """Create a soil microbiome record for a field, auto-classifying health from respiration rate."""
    _get_field(farm_id, field_id, db)
    classification = classify_microbiome(body.respiration_rate)
    record = MicrobiomeRecord(
        field_id=field_id,
        classification=classification,
        **body.model_dump(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=list[MicrobiomeOut])
def list_microbiome_records(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    """List all microbiome records for a field, ordered by most recent sample date."""
    _get_field(farm_id, field_id, db)
    return (
        db.query(MicrobiomeRecord)
        .filter(MicrobiomeRecord.field_id == field_id)
        .order_by(MicrobiomeRecord.sampled_at.desc())
        .all()
    )
