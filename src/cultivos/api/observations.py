"""Farmer observation log endpoints.

POST /api/farms/{farm_id}/fields/{field_id}/observations
GET  /api/farms/{farm_id}/fields/{field_id}/observations

Captures farmer ground-truth observations — completes the data loop
(drone + sensor + farmer eyes). Required for WhatsApp integration.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from cultivos.db.models import Farm, FarmerObservation, Field
from cultivos.db.session import get_db
from cultivos.models.observation import (
    FarmerObservationIn,
    FarmerObservationListOut,
    FarmerObservationOut,
)
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}/observations",
    tags=["observations"],
)


def _get_field(farm_id: int, field_id: int, db: Session) -> Field:
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@router.post("", response_model=FarmerObservationOut, status_code=201)
def create_observation(
    farm_id: int,
    field_id: int,
    payload: FarmerObservationIn,
    db: Session = Depends(get_db),
) -> FarmerObservationOut:
    """Record a farmer ground-truth observation for a field."""
    field = _get_field(farm_id, field_id, db)

    obs = FarmerObservation(
        field_id=field.id,
        observation_es=payload.observation_es,
        observation_type=payload.observation_type,
        crop_stage=payload.crop_stage,
        created_at=datetime.utcnow(),
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return FarmerObservationOut.model_validate(obs)


@router.get("", response_model=FarmerObservationListOut)
def list_observations(
    farm_id: int,
    field_id: int,
    type: Optional[str] = Query(None, description="Filter by observation_type: problem | success | neutral"),
    db: Session = Depends(get_db),
) -> FarmerObservationListOut:
    """List farmer observations for a field, newest first. Optional ?type= filter."""
    field = _get_field(farm_id, field_id, db)

    q = db.query(FarmerObservation).filter(FarmerObservation.field_id == field.id)
    if type is not None:
        q = q.filter(FarmerObservation.observation_type == type)

    records = q.order_by(FarmerObservation.created_at.desc()).all()

    items = [FarmerObservationOut.model_validate(r) for r in records]
    return FarmerObservationListOut(field_id=field.id, total=len(items), items=items)
