"""Field one-sentence Spanish next-action endpoint — WhatsApp-sized voice-ready response."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field
from cultivos.db.session import get_db
from cultivos.models.field_accion import FieldAccionOut
from cultivos.services.intelligence.field_accion import compute_field_accion

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}",
    tags=["intelligence"],
)


@router.get(
    "/accion-siguiente",
    response_model=FieldAccionOut,
    description="One-sentence Spanish next-action — WhatsApp reply budget sized for farmer cognitive load.",
)
def get_field_accion_siguiente(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = (
        db.query(Field)
        .filter(Field.id == field_id, Field.farm_id == farm_id)
        .first()
    )
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return compute_field_accion(field, db)
