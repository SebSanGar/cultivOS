"""Crop rotation endpoints — nested under /api/farms/{farm_id}/fields/{field_id}/rotation."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.models import Farm, Field, SoilAnalysis
from cultivos.db.session import get_db
from cultivos.models.rotation import MultiYearPlanOut, RotationPlanOut
from cultivos.services.intelligence.rotation import (
    SoilInput,
    plan_multi_year_rotation,
    plan_rotation,
)

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}/rotation",
    tags=["rotation"],
    dependencies=[Depends(get_current_user)]
)


def _get_field(farm_id: int, field_id: int, db: Session) -> Field:
    """Validate farm and field exist and are linked."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@router.get("/multi-year", response_model=MultiYearPlanOut)
def get_multi_year_plan(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    """Generate a 3-year rotation plan with soil OM projections and milpa recommendations.

    Returns 6 seasons spanning 3 years with projected soil organic matter per season.
    Includes milpa (Three Sisters) recommendation for compatible Jalisco crops.
    """
    field = _get_field(farm_id, field_id, db)

    if not field.crop_type:
        raise HTTPException(
            status_code=422,
            detail="Field has no crop_type set. Update the field first.",
        )

    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    region = (farm.state or "Jalisco").lower()

    latest_soil = (
        db.query(SoilAnalysis)
        .filter(SoilAnalysis.field_id == field_id)
        .order_by(SoilAnalysis.sampled_at.desc())
        .first()
    )

    soil_input: SoilInput | None = None
    if latest_soil:
        soil_input = SoilInput(
            organic_matter_pct=latest_soil.organic_matter_pct,
            nitrogen_ppm=latest_soil.nitrogen_ppm,
            ph=latest_soil.ph,
        )

    result = plan_multi_year_rotation(
        last_crop=field.crop_type,
        region=region,
        soil=soil_input,
    )

    return MultiYearPlanOut(
        field_id=field_id,
        last_crop=field.crop_type,
        region=region,
        **result,
    )


@router.get("", response_model=RotationPlanOut)
def get_rotation_plan(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    """Generate a crop rotation plan based on current crop and soil data.

    Uses the field's crop_type as last_crop and the farm's state as region.
    Fetches latest soil analysis if available.
    Returns 422 if no crop_type is set on the field.
    """
    field = _get_field(farm_id, field_id, db)

    if not field.crop_type:
        raise HTTPException(
            status_code=422,
            detail="Field has no crop_type set. Update the field first.",
        )

    # Get farm for region
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    region = (farm.state or "Jalisco").lower()

    # Fetch latest soil analysis
    latest_soil = (
        db.query(SoilAnalysis)
        .filter(SoilAnalysis.field_id == field_id)
        .order_by(SoilAnalysis.sampled_at.desc())
        .first()
    )

    soil_input: SoilInput | None = None
    if latest_soil:
        soil_input = SoilInput(
            organic_matter_pct=latest_soil.organic_matter_pct,
            nitrogen_ppm=latest_soil.nitrogen_ppm,
            ph=latest_soil.ph,
        )

    plan = plan_rotation(
        last_crop=field.crop_type,
        region=region,
        soil=soil_input,
    )

    return RotationPlanOut(
        field_id=field_id,
        last_crop=field.crop_type,
        region=region,
        plan=plan,
    )
