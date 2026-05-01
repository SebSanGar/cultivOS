"""Field critical/high alerts endpoint — voice-ready Spanish list."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field
from cultivos.db.session import get_db
from cultivos.models.field_alertas_criticas import AlertasCriticasOut
from cultivos.services.intelligence.field_alertas_criticas import compute_alertas_criticas

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}",
    tags=["intelligence"],
)


@router.get(
    "/alertas-criticas",
    response_model=AlertasCriticasOut,
    description="Open critical/high alerts for a field — Spanish sentences, voice-ready.",
)
def get_alertas_criticas(
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
    return compute_alertas_criticas(field, db)
