"""Growth stage endpoint — computes phenology stage for a field."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.models import Farm, Field
from cultivos.db.session import get_db
from cultivos.models.growth_stage import GrowthStageOut
from cultivos.services.crop.phenology import compute_growth_stage, get_all_stages_info

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}/growth-stage",
    tags=["growth-stage"],
    dependencies=[Depends(get_current_user)]
)


@router.get("", response_model=GrowthStageOut)
def get_growth_stage(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    """Compute current growth stage based on field's planted_at date and crop type."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    if not field.planted_at:
        raise HTTPException(
            status_code=422,
            detail="No planted_at date set for this field. Update the field with a planting date.",
        )

    crop = field.crop_type or "desconocido"
    result = compute_growth_stage(crop, field.planted_at)
    all_stages = get_all_stages_info(crop, current_stage=result["stage"])

    return GrowthStageOut(
        crop_type=crop,
        stage=result["stage"],
        stage_es=result["stage_es"],
        days_since_planting=result["days_since_planting"],
        days_in_stage=result["days_in_stage"],
        days_until_next_stage=result["days_until_next_stage"],
        water_multiplier=result["water_multiplier"],
        nutrient_focus=result["nutrient_focus"],
        all_stages=all_stages,
    )
