"""Organic certification readiness endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.session import get_db
from cultivos.models.certification import CertificationReadinessOut
from cultivos.services.intelligence.certification import compute_certification_readiness

router = APIRouter(tags=["intelligence"], dependencies=[Depends(get_current_user)])


@router.get(
    "/api/farms/{farm_id}/certification-readiness",
    response_model=CertificationReadinessOut,
)
def get_certification_readiness(
    farm_id: int,
    db: Session = Depends(get_db),
) -> CertificationReadinessOut:
    """Check organic certification readiness for a farm.

    Returns a 4-check scorecard:
    - synthetic_inputs_free: no synthetic treatments on any field
    - treatment_organic_only: same (certification-language alias)
    - soc_trend_positive: soil organic carbon is stable or rising (needs 2+ samples)
    - cover_crop_days_gte_90: cover crop use equivalent to >= 90 days

    overall_pct (0-100) = fraction of checks that pass.
    FODECIJAL: concrete evidence that cultivOS drives certified organic outcomes.
    """
    result = compute_certification_readiness(farm_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    return CertificationReadinessOut(**result)
