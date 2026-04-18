"""Field Spanish plain-language summary endpoint — voice-ready for WhatsApp."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field
from cultivos.db.session import get_db
from cultivos.models.field_resumen import FieldResumenOut
from cultivos.services.intelligence.field_resumen import compute_field_resumen

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}",
    tags=["intelligence"],
)


@router.get(
    "/resumen",
    response_model=FieldResumenOut,
    description="Farmer-friendly 3-sentence Spanish summary of field state — voice-ready for WhatsApp.",
)
def get_field_resumen(
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
    return compute_field_resumen(field, db)
