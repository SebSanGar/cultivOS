"""Cooperative data completeness aggregate endpoint.

GET /api/cooperatives/{coop_id}/data-completeness — rolls up per-farm
compute_data_completeness across member farms. Returns overall score,
worst_farm, and per-grade counts (A/B/C/D).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.models import Cooperative
from cultivos.db.session import get_db
from cultivos.models.coop_data_completeness import (
    CoopDataCompletenessOut,
    GradeCounts,
    WorstFarmEntry,
)
from cultivos.services.intelligence.coop_data_completeness import (
    compute_coop_data_completeness,
)

router = APIRouter(
    prefix="/api/cooperatives/{coop_id}/data-completeness",
    tags=["intelligence"],
    dependencies=[Depends(get_current_user)]
)


@router.get(
    "",
    response_model=CoopDataCompletenessOut,
    description=(
        "Cooperative-level data completeness aggregate: avg score across "
        "member farms, worst farm, and per-grade counts (A>=80, B 60-79, "
        "C 40-59, D<40)."
    ),
)
def get_coop_data_completeness(
    coop_id: int,
    db: Session = Depends(get_db),
):
    coop = db.query(Cooperative).filter(Cooperative.id == coop_id).first()
    if not coop:
        raise HTTPException(status_code=404, detail="Cooperative not found")

    result = compute_coop_data_completeness(coop_id, db)
    return CoopDataCompletenessOut(
        cooperative_id=result["cooperative_id"],
        total_farms=result["total_farms"],
        overall_completeness_pct=result["overall_completeness_pct"],
        worst_farm=WorstFarmEntry(**result["worst_farm"]) if result["worst_farm"] else None,
        farms_by_grade=GradeCounts(**result["farms_by_grade"]),
    )
