"""#207 Farm ancestral method adoption log endpoints.

POST /api/farms/{farm_id}/tek-adoptions
GET  /api/farms/{farm_id}/tek-adoptions
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.models import Farm
from cultivos.db.session import get_db
from cultivos.models.tek_adoption import (
    TEKAdoptionIn,
    TEKAdoptionListOut,
    TEKAdoptionOut,
)
from cultivos.services.intelligence.tek_adoption import (
    create_adoption,
    list_adoptions,
)

router = APIRouter(
    prefix="/api/farms/{farm_id}/tek-adoptions",
    tags=["tek-adoption"],
    dependencies=[Depends(get_current_user)]
)


def _get_farm(farm_id: int, db: Session) -> Farm:
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm


@router.post(
    "",
    response_model=TEKAdoptionOut,
    status_code=201,
    description="Record a farm's adoption of an ancestral/TEK method on one or more of its fields.",
)
def post_tek_adoption(
    farm_id: int,
    payload: TEKAdoptionIn,
    db: Session = Depends(get_db),
) -> TEKAdoptionOut:
    """Record a farm's adoption of an ancestral/TEK method."""
    farm = _get_farm(farm_id, db)
    try:
        row, method = create_adoption(
            farm=farm,
            method_name=payload.method_name,
            adopted_at=payload.adopted_at,
            fields_applied=payload.fields_applied,
            farmer_notes_es=payload.farmer_notes_es or "",
            db=db,
        )
    except ValueError as e:
        kind = str(e)
        if kind == "method":
            raise HTTPException(status_code=404, detail="Ancestral method not found")
        if kind == "field":
            raise HTTPException(status_code=404, detail="Field not found or not in this farm")
        raise
    return TEKAdoptionOut(
        id=row.id,
        method_name=row.method_name,
        adopted_at=row.adopted_at,
        fields_count=len(row.fields_applied or []),
        farmer_notes_es=row.farmer_notes_es or "",
        ecological_benefit=method.ecological_benefit,
    )


@router.get(
    "",
    response_model=TEKAdoptionListOut,
    description="List a farm's ancestral method adoptions, newest first, with ecological benefit.",
)
def get_tek_adoptions(
    farm_id: int,
    db: Session = Depends(get_db),
) -> TEKAdoptionListOut:
    """List a farm's ancestral method adoptions."""
    farm = _get_farm(farm_id, db)
    result = list_adoptions(farm, db)
    return TEKAdoptionListOut(**result)
