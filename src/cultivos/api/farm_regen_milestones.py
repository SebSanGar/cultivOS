"""Farm regenerative milestone tracker endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.session import get_db
from cultivos.models.farm_regen_milestones import FarmRegenMilestonesOut
from cultivos.services.intelligence.farm_regen_milestones import (
    compute_farm_regen_milestones,
)

router = APIRouter(tags=["intelligence"], dependencies=[Depends(get_current_user)])


@router.get(
    "/api/farms/{farm_id}/regen-milestones",
    response_model=FarmRegenMilestonesOut,
)
def get_farm_regen_milestones(
    farm_id: int,
    db: Session = Depends(get_db),
) -> FarmRegenMilestonesOut:
    """Regenerative progress milestones for a farm — 7 ordered achievements."""
    result = compute_farm_regen_milestones(farm_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    return FarmRegenMilestonesOut(**result)
