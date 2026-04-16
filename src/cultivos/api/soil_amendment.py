"""Soil amendment calculator API — organic prescriptions from soil analysis."""

from fastapi import APIRouter, Depends

from cultivos.auth import get_current_user
from cultivos.models.soil_amendment import SoilAmendmentRequest, SoilAmendmentResponse
from cultivos.services.intelligence.soil_amendment import calculate_soil_amendments

router = APIRouter(prefix="/api/intel", tags=["intelligence"], dependencies=[Depends(get_current_user)])


@router.post("/soil-amendment", response_model=SoilAmendmentResponse)
def compute_soil_amendment(body: SoilAmendmentRequest):
    """Calculate organic soil amendments to reach target values.

    Given current soil values (pH, organic matter, N/P/K) and optional targets,
    returns a prescription of organic amendments with quantities per hectare
    and estimated costs in MXN.
    """
    result = calculate_soil_amendments(
        current_ph=body.current_ph,
        target_ph=body.target_ph,
        current_om_pct=body.current_om_pct,
        target_om_pct=body.target_om_pct,
        current_n_ppm=body.current_n_ppm,
        target_n_ppm=body.target_n_ppm,
        current_p_ppm=body.current_p_ppm,
        target_p_ppm=body.target_p_ppm,
        current_k_ppm=body.current_k_ppm,
        target_k_ppm=body.target_k_ppm,
    )
    return result
