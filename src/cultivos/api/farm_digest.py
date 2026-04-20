"""Farm-level Spanish daily digest endpoint — WhatsApp paste-ready."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Farm
from cultivos.db.session import get_db
from cultivos.models.farm_digest import FarmDigestOut
from cultivos.services.intelligence.farm_digest import compute_farm_digest

router = APIRouter(
    prefix="/api/farms/{farm_id}",
    tags=["intelligence"],
)


@router.get(
    "/digest-whatsapp",
    response_model=FarmDigestOut,
    description="100-200 char Spanish digest of all fields — paste into WhatsApp.",
)
def get_farm_digest(
    farm_id: int,
    db: Session = Depends(get_db),
):
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return compute_farm_digest(farm, db)
