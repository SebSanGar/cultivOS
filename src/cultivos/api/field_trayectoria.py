"""Field 7-day Spanish trajectory endpoint — WhatsApp-sized voice-ready response."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field
from cultivos.db.session import get_db
from cultivos.models.field_trayectoria import FieldTrayectoriaOut
from cultivos.services.intelligence.field_trayectoria import compute_field_trayectoria

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}",
    tags=["intelligence"],
)


@router.get(
    "/trayectoria-semana",
    response_model=FieldTrayectoriaOut,
    description="7-day health trajectory in Spanish — trend, alerts, treatments, narrative.",
)
def get_field_trayectoria_semana(
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
    return compute_field_trayectoria(field, db)
