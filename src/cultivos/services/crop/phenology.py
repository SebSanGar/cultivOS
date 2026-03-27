"""Pure phenology service — computes crop growth stage from planted date.

No HTTP, no database, no side effects. Date in, stage info out.
Growth stages: siembra, vegetativo, floracion, fructificacion, cosecha.
Stage durations calibrated for Jalisco, Mexico conditions.
"""

from datetime import datetime
from typing import TypedDict


class GrowthStageResult(TypedDict):
    stage: str  # siembra, vegetativo, floracion, fructificacion, cosecha
    stage_es: str  # display name in Spanish
    days_since_planting: int
    days_in_stage: int
    days_until_next_stage: int | None
    water_multiplier: float  # multiplier for base irrigation need
    nutrient_focus: str  # what nutrients matter most at this stage


# Stage definitions per crop: list of (stage_name, end_day, water_mult, nutrient_focus)
# end_day is the last day of that stage (inclusive)
_STAGE_DEFS = [
    ("siembra", "Siembra", 0.7, "Fosforo para raices, riego suave y frecuente"),
    ("vegetativo", "Vegetativo", 1.0, "Nitrogeno para crecimiento foliar"),
    ("floracion", "Floracion", 1.3, "Potasio y fosforo para flores, riego critico"),
    ("fructificacion", "Fructificacion", 1.1, "Potasio para frutos, calcio para firmeza"),
    ("cosecha", "Cosecha", 0.5, "Reducir riego, dejar madurar"),
]

# Days at which each stage ends, per crop (cumulative days from planting)
# Format: [siembra_end, vegetativo_end, floracion_end, fructificacion_end, cosecha_start]
_CROP_STAGE_DAYS: dict[str, list[int]] = {
    "maiz":       [15, 55, 80, 120, 150],
    "frijol":     [12, 40, 60,  85, 100],
    "calabaza":   [12, 45, 65,  95, 120],
    "chile":      [20, 55, 75, 110, 140],
    "jitomate":   [15, 45, 65,  95, 120],
    "aguacate":   [60, 180, 240, 300, 365],  # perennial, annual cycle
    "agave":      [90, 365, 730, 2190, 2555],  # 7-year cycle
    "sorgo":      [12, 40, 60,  90, 110],
    "garbanzo":   [15, 45, 65,  90, 110],
    "cana":       [30, 120, 180, 300, 365],
    "nopal":      [30, 90, 120, 180, 240],
}

_DEFAULT_STAGE_DAYS = [15, 50, 75, 110, 140]


def compute_growth_stage(
    crop_type: str,
    planted_at: datetime | None,
    reference_date: datetime | None = None,
) -> GrowthStageResult | None:
    """Compute the current growth stage for a crop based on planting date.

    Args:
        crop_type: Crop being grown (maiz, frijol, etc.)
        planted_at: When the crop was planted. Returns None if not set.
        reference_date: Date to compute stage for (defaults to now).

    Returns:
        GrowthStageResult with stage info and multipliers, or None if no planted_at.
    """
    if planted_at is None:
        return None

    now = reference_date or datetime.utcnow()
    days_elapsed = max(0, (now - planted_at).days)

    stage_days = _CROP_STAGE_DAYS.get((crop_type or "").lower(), _DEFAULT_STAGE_DAYS)

    # Find which stage we're in
    stage_idx = 0
    for i, end_day in enumerate(stage_days):
        if days_elapsed <= end_day:
            stage_idx = i
            break
    else:
        stage_idx = len(stage_days) - 1  # past all stages = cosecha

    stage_name, stage_es, water_mult, nutrient_focus = _STAGE_DEFS[stage_idx]

    # Days in current stage
    stage_start = stage_days[stage_idx - 1] if stage_idx > 0 else 0
    days_in_stage = days_elapsed - stage_start

    # Days until next stage
    if stage_idx < len(stage_days) - 1:
        days_until_next = stage_days[stage_idx] - days_elapsed
    else:
        days_until_next = None

    return GrowthStageResult(
        stage=stage_name,
        stage_es=stage_es,
        days_since_planting=days_elapsed,
        days_in_stage=days_in_stage,
        days_until_next_stage=days_until_next,
        water_multiplier=water_mult,
        nutrient_focus=nutrient_focus,
    )
