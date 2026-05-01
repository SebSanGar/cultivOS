"""Farm daily Spanish greeting endpoint — WhatsApp paste-ready."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Farm
from cultivos.db.session import get_db
from cultivos.models.farm_saludo_diario import SaludoDiarioOut
from cultivos.services.intelligence.farm_saludo_diario import compute_saludo_diario

router = APIRouter(
    prefix="/api/farms/{farm_id}",
    tags=["intelligence"],
)


@router.get(
    "/saludo-diario",
    response_model=SaludoDiarioOut,
    description="Two-sentence Spanish daily greeting — paste into WhatsApp.",
)
def get_saludo_diario(
    farm_id: int,
    db: Session = Depends(get_db),
):
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return compute_saludo_diario(farm, db)
