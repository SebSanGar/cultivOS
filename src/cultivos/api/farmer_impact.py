"""Farmer impact summary — per-farm journey metrics and health improvement."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Farm
from cultivos.db.session import get_db
from cultivos.models.intel import FarmerImpactOut
from cultivos.services.intelligence.analytics import compute_farmer_impact

router = APIRouter(
    prefix="/api/farms/{farm_id}",
    tags=["farmer-impact"],
)


def _get_farm(farm_id: int, db: Session) -> Farm:
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm


@router.get("/farmer-impact", response_model=FarmerImpactOut)
def get_farmer_impact(
    farm_id: int,
    db: Session = Depends(get_db),
):
    """Aggregate farmer journey metrics — days since onboard, recommendations,
    treatments applied, health improvement, estimated savings."""
    _get_farm(farm_id, db)
    result = compute_farmer_impact(db, farm_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    return FarmerImpactOut(**result)
