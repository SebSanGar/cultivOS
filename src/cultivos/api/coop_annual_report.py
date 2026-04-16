"""Cooperative annual report aggregate endpoint.

GET /api/cooperatives/{coop_id}/annual-report?year= — coop-level rollup of
per-farm annual reports (avg_health_change, total CO2e, total treatments,
best_farm by health delta, farms_improved_count).
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.models import Cooperative
from cultivos.db.session import get_db
from cultivos.models.coop_annual_report import (
    BestFarmEntry,
    CoopAnnualReportOut,
)
from cultivos.services.intelligence.coop_annual_report import (
    compute_coop_annual_report,
)

router = APIRouter(
    prefix="/api/cooperatives/{coop_id}/annual-report",
    tags=["intelligence"],
    dependencies=[Depends(get_current_user)]
)


@router.get(
    "",
    response_model=CoopAnnualReportOut,
    description=(
        "Cooperative-level annual report aggregating per-farm annual reports: "
        "avg_health_change across member farms, total CO2e sequestered, total "
        "treatments applied, best_farm by health delta, farms_improved_count."
    ),
)
def get_coop_annual_report(
    coop_id: int,
    year: Optional[int] = Query(None, description="Calendar year (defaults to current)"),
    db: Session = Depends(get_db),
):
    coop = db.query(Cooperative).filter(Cooperative.id == coop_id).first()
    if not coop:
        raise HTTPException(status_code=404, detail="Cooperative not found")

    target_year = year or datetime.utcnow().year
    result = compute_coop_annual_report(coop_id, target_year, db)
    return CoopAnnualReportOut(
        cooperative_id=result["cooperative_id"],
        year=result["year"],
        total_farms=result["total_farms"],
        total_fields=result["total_fields"],
        avg_health_change=result["avg_health_change"],
        total_co2e_sequestered_t=result["total_co2e_sequestered_t"],
        total_treatments_applied=result["total_treatments_applied"],
        best_farm=BestFarmEntry(**result["best_farm"]) if result["best_farm"] else None,
        farms_improved_count=result["farms_improved_count"],
        farms_total=result["farms_total"],
    )
