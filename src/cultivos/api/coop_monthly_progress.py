"""Cooperative monthly progress snapshot endpoint.

GET /api/cooperatives/{coop_id}/monthly-progress?months=6 — per-month
avg_health, treatments, observations, and regen_score across all member
farms. Grant reporting endpoint showing month-over-month cooperative
improvement for FODECIJAL narrative.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.models import Cooperative
from cultivos.db.session import get_db
from cultivos.models.coop_monthly_progress import (
    CoopMonthlyProgressOut,
    MonthlyProgressEntry,
)
from cultivos.services.intelligence.coop_monthly_progress import (
    compute_coop_monthly_progress,
)

router = APIRouter(
    prefix="/api/cooperatives/{coop_id}/monthly-progress",
    tags=["intelligence"],
    dependencies=[Depends(get_current_user)]
)


@router.get(
    "",
    response_model=CoopMonthlyProgressOut,
    description=(
        "Cooperative monthly progress snapshot over the last N months. "
        "Returns avg_health, treatment counts, farmer observations, and "
        "regen_score per month across all member farms. Used for grant "
        "progress narratives (month-over-month cooperative improvement)."
    ),
)
def get_coop_monthly_progress(
    coop_id: int,
    months: int = Query(6, ge=1, le=24),
    db: Session = Depends(get_db),
):
    coop = db.query(Cooperative).filter(Cooperative.id == coop_id).first()
    if not coop:
        raise HTTPException(status_code=404, detail="Cooperative not found")

    result = compute_coop_monthly_progress(coop_id, months, db)
    return CoopMonthlyProgressOut(
        cooperative_id=result["cooperative_id"],
        months_requested=result["months_requested"],
        months=[MonthlyProgressEntry(**m) for m in result["months"]],
        overall_trend=result["overall_trend"],
    )
