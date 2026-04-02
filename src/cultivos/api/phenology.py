"""Phenology calendar endpoint — returns all crop stage timelines."""

from fastapi import APIRouter

from cultivos.services.crop.phenology import get_all_stages_info, _CROP_STAGE_DAYS

router = APIRouter(prefix="/api/phenology", tags=["phenology"])


@router.get("/calendar")
def get_phenology_calendar():
    """Return phenology stage timelines for all supported crop types.

    Used by the /calendario page to render Gantt-like crop stage bars.
    """
    crops = []
    for crop_type in sorted(_CROP_STAGE_DAYS.keys()):
        stages = get_all_stages_info(crop_type)
        total_days = stages[-1]["end_day"] if stages else 0
        crops.append({
            "crop_type": crop_type,
            "total_days": total_days,
            "stages": [
                {
                    "name": s["name"],
                    "name_es": s["name_es"],
                    "start_day": s["start_day"],
                    "end_day": s["end_day"],
                    "water_multiplier": s["water_multiplier"],
                    "nutrient_focus": s["nutrient_focus"],
                }
                for s in stages
            ],
        })
    return {"crops": crops}
