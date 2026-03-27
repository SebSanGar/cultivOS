"""Pure irrigation optimization — computes daily water schedule from weather, soil, and thermal data.

No HTTP, no database, no side effects. Dicts in, dict out.
"""

from typing import TypedDict

# Base water needs per crop (liters/ha/day) in Jalisco conditions
CROP_BASE_WATER: dict[str, float] = {
    "maiz": 5000.0,
    "frijol": 3500.0,
    "agave": 2000.0,
    "aguacate": 6000.0,
    "jitomate": 5500.0,
    "calabaza": 4000.0,
    "chile": 4500.0,
    "sorgo": 4000.0,
}

DEFAULT_BASE_WATER = 4500.0

# Soil texture drainage multipliers — sandy drains fast (needs more water), clay retains
SOIL_TEXTURE_MULTIPLIER: dict[str, float] = {
    "sand": 1.4,
    "sandy_loam": 1.2,
    "loam": 1.0,
    "clay_loam": 0.85,
    "clay": 0.7,
    "silt": 0.9,
}

# Rainfall offset: mm of rain -> equivalent liters/ha saved
RAINFALL_TO_LITERS_PER_HA = 10_000.0  # 1mm rain on 1ha = 10,000 liters

SCHEDULE_DAYS = 7  # Generate a 7-day schedule


class DaySchedule(TypedDict):
    day: int
    liters_per_ha: float
    nota: str


class IrrigationResult(TypedDict):
    crop_type: str
    hectares: float
    schedule: list[DaySchedule]
    liters_total_per_ha: float
    urgencia: str  # alta, media, baja
    recomendacion: str


def compute_irrigation_schedule(
    crop_type: str,
    hectares: float,
    soil: dict | None,
    weather: dict | None,
    thermal: dict | None,
    growth_stage: str | None = None,
) -> IrrigationResult:
    """Compute a 7-day irrigation schedule based on available data.

    Args:
        crop_type: Crop being grown (maiz, agave, etc.)
        hectares: Field size
        soil: {texture, moisture_pct} or None
        weather: {temp_c, humidity_pct, recent_rainfall_mm} or None
        thermal: {stress_pct, irrigation_deficit} or None

    Returns:
        IrrigationResult with daily schedule and totals.
    """
    # Step 1: Base water need for crop
    base = CROP_BASE_WATER.get(crop_type or "", DEFAULT_BASE_WATER)

    # Step 2: Soil texture adjustment
    texture = (soil or {}).get("texture", "loam") or "loam"
    soil_mult = SOIL_TEXTURE_MULTIPLIER.get(texture.lower(), 1.0)
    adjusted = base * soil_mult

    # Step 2.5: Growth stage adjustment
    if growth_stage:
        from cultivos.services.crop.phenology import _STAGE_DEFS
        stage_multipliers = {s[0]: s[2] for s in _STAGE_DEFS}
        stage_mult = stage_multipliers.get(growth_stage, 1.0)
        adjusted *= stage_mult

    # Step 3: Soil moisture adjustment — high existing moisture reduces need
    moisture_pct = (soil or {}).get("moisture_pct")
    if moisture_pct is not None:
        if moisture_pct > 40:
            adjusted *= 0.6  # well-hydrated soil
        elif moisture_pct > 25:
            adjusted *= 0.85  # moderate
        # below 25% = full need (multiplier 1.0)

    # Step 4: Weather adjustments
    temp_c = (weather or {}).get("temp_c", 25.0) or 25.0
    humidity_pct = (weather or {}).get("humidity_pct", 50.0) or 50.0
    rainfall_mm = (weather or {}).get("recent_rainfall_mm", 0.0) or 0.0

    # Temperature scaling: above 35C increases evaporation significantly
    if temp_c > 35:
        adjusted *= 1.3
    elif temp_c > 30:
        adjusted *= 1.1

    # Low humidity increases evaporation
    if humidity_pct < 30:
        adjusted *= 1.2
    elif humidity_pct > 70:
        adjusted *= 0.9

    # Rainfall offset: subtract equivalent water from recent rain
    rain_offset_per_day = 0.0
    if rainfall_mm > 0:
        rain_liters = rainfall_mm * RAINFALL_TO_LITERS_PER_HA
        rain_offset_per_day = rain_liters / SCHEDULE_DAYS

    # Step 5: Thermal stress adjustment
    if thermal:
        stress_pct = thermal.get("stress_pct", 0.0)
        deficit = thermal.get("irrigation_deficit", False)
        if deficit:
            adjusted *= 1.25
        if stress_pct > 40:
            adjusted *= 1.15

    # Step 6: Build 7-day schedule
    schedule: list[DaySchedule] = []
    for day_num in range(1, SCHEDULE_DAYS + 1):
        daily = max(0.0, adjusted - rain_offset_per_day)
        daily = round(daily, 0)

        if daily == 0:
            nota = "Sin riego necesario — lluvia reciente suficiente"
        elif daily > base * 1.2:
            nota = "Riego incrementado — condiciones de estres"
        else:
            nota = "Riego normal"

        schedule.append(DaySchedule(day=day_num, liters_per_ha=daily, nota=nota))

    total = sum(d["liters_per_ha"] for d in schedule)

    # Step 7: Urgency classification
    if thermal and thermal.get("irrigation_deficit"):
        urgencia = "alta"
    elif temp_c > 35 and rainfall_mm < 2:
        urgencia = "alta"
    elif temp_c > 30 and humidity_pct < 40:
        urgencia = "media"
    else:
        urgencia = "baja"

    # Step 8: Human-readable recommendation in Spanish
    if urgencia == "alta":
        recomendacion = (
            f"Condiciones de sequia detectadas. Se recomienda riego diario de "
            f"{schedule[0]['liters_per_ha']:.0f} litros/ha para {crop_type or 'cultivo'}. "
            f"Priorizar riego temprano (antes de 8am) para minimizar evaporacion."
        )
    elif rainfall_mm > 10:
        recomendacion = (
            f"Lluvia reciente ({rainfall_mm:.0f}mm) reduce necesidad de riego. "
            f"Monitorear humedad del suelo antes de regar."
        )
    else:
        recomendacion = (
            f"Condiciones normales. Riego programado de "
            f"{schedule[0]['liters_per_ha']:.0f} litros/ha/dia para {crop_type or 'cultivo'}."
        )

    return IrrigationResult(
        crop_type=crop_type or "desconocido",
        hectares=hectares,
        schedule=schedule,
        liters_total_per_ha=round(total, 0),
        urgencia=urgencia,
        recomendacion=recomendacion,
    )
