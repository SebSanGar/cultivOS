"""Cooperative crop diversity score endpoint.

GET /api/cooperatives/{coop_id}/crop-diversity — distinct crops, Shannon
diversity index, and top 3 crops by hectares across a cooperative's farms.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Cooperative
from cultivos.db.session import get_db
from cultivos.models.coop_crop_diversity import (
    CoopCropDiversityOut,
    CoopFarmDiversityEntry,
    TopCropEntry,
)
from cultivos.services.intelligence.coop_crop_diversity import (
    compute_coop_crop_diversity,
)

router = APIRouter(
    prefix="/api/cooperatives/{coop_id}/crop-diversity",
    tags=["intelligence"],
)


@router.get(
    "",
    response_model=CoopCropDiversityOut,
    description=(
        "Distinct crop counts (coop + per farm), Shannon diversity index on "
        "hectare-weighted crop proportions, and top 3 crops by hectares across "
        "the cooperative's member farms."
    ),
)
def get_coop_crop_diversity(coop_id: int, db: Session = Depends(get_db)):
    coop = db.query(Cooperative).filter(Cooperative.id == coop_id).first()
    if not coop:
        raise HTTPException(status_code=404, detail="Cooperative not found")

    result = compute_coop_crop_diversity(coop_id, db)
    return CoopCropDiversityOut(
        cooperative_id=result["cooperative_id"],
        total_farms=result["total_farms"],
        total_fields=result["total_fields"],
        distinct_crops_coop=result["distinct_crops_coop"],
        shannon_index=result["shannon_index"],
        top_crops=[TopCropEntry(**c) for c in result["top_crops"]],
        farms=[CoopFarmDiversityEntry(**f) for f in result["farms"]],
    )
