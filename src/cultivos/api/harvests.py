"""Harvest record endpoints.

POST /api/farms/{farm_id}/fields/{field_id}/harvests
GET  /api/farms/{farm_id}/fields/{field_id}/harvests

When a harvest is created, the most recent unresolved yield PredictionSnapshot
for the field is updated with the actual yield so prediction accuracy can be
computed.
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, HarvestRecord, PredictionSnapshot
from cultivos.db.session import get_db
from cultivos.models.harvest import HarvestRecordIn, HarvestRecordOut

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}/harvests",
    tags=["harvests"],
)


def _get_field(farm_id: int, field_id: int, db: Session) -> Field:
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


def _resolve_yield_prediction(field_id: int, actual_yield_kg: float, db: Session) -> None:
    """Update the most recent unresolved yield prediction with the actual value."""
    ps = (
        db.query(PredictionSnapshot)
        .filter(
            PredictionSnapshot.field_id == field_id,
            PredictionSnapshot.prediction_type == "yield",
            PredictionSnapshot.actual_value.is_(None),
        )
        .order_by(PredictionSnapshot.predicted_at.desc())
        .first()
    )
    if ps:
        ps.actual_value = actual_yield_kg
        ps.resolved_at = datetime.utcnow()
        db.commit()


def _build_out(record: HarvestRecord, db: Session) -> HarvestRecordOut:
    """Build HarvestRecordOut, computing predicted_vs_actual_kg if possible."""
    predicted_vs_actual: float | None = None

    # Find the most recent resolved yield prediction for this field
    ps = (
        db.query(PredictionSnapshot)
        .filter(
            PredictionSnapshot.field_id == record.field_id,
            PredictionSnapshot.prediction_type == "yield",
            PredictionSnapshot.actual_value.isnot(None),
        )
        .order_by(PredictionSnapshot.resolved_at.desc())
        .first()
    )
    if ps and ps.actual_value is not None and ps.predicted_value is not None:
        predicted_vs_actual = ps.actual_value - ps.predicted_value

    return HarvestRecordOut(
        id=record.id,
        field_id=record.field_id,
        crop_type=record.crop_type,
        harvest_date=record.harvest_date,
        actual_yield_kg=record.actual_yield_kg,
        notes=record.notes,
        predicted_vs_actual_kg=predicted_vs_actual,
        created_at=record.created_at,
    )


@router.post("", response_model=HarvestRecordOut, status_code=201)
def create_harvest(
    farm_id: int,
    field_id: int,
    payload: HarvestRecordIn,
    db: Session = Depends(get_db),
) -> HarvestRecordOut:
    """Record an actual harvest yield for a field.

    Also resolves the most recent open yield PredictionSnapshot for this field
    so prediction accuracy metrics stay current.
    """
    field = _get_field(farm_id, field_id, db)

    record = HarvestRecord(
        field_id=field.id,
        crop_type=payload.crop_type,
        harvest_date=datetime.combine(payload.harvest_date, datetime.min.time()),
        actual_yield_kg=payload.actual_yield_kg,
        notes=payload.notes,
        created_at=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # Link to open yield prediction
    _resolve_yield_prediction(field.id, payload.actual_yield_kg, db)

    return _build_out(record, db)


@router.get("", response_model=List[HarvestRecordOut])
def list_harvests(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
) -> List[HarvestRecordOut]:
    """List all harvest records for a field, newest first."""
    _get_field(farm_id, field_id, db)

    records = (
        db.query(HarvestRecord)
        .filter(HarvestRecord.field_id == field_id)
        .order_by(HarvestRecord.harvest_date.desc())
        .all()
    )
    return [_build_out(r, db) for r in records]
