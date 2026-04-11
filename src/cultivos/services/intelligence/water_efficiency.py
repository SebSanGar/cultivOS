"""Pure water use efficiency service.

Estimates water waste, optimal irrigation, and stress index from weather + thermal data.
No HTTP, no database, no side effects. Dicts in, dict out.
"""

from typing import TypedDict

# mm of rainfall per day that satisfies base water need
RAINFALL_FULL_COVERAGE_MM = 20.0  # 20mm/day = no additional irrigation needed

# Optimal irrigation per crop (mm/day)
CROP_OPTIMAL_IRRIGATION_MM: dict[str, float] = {
    "maiz": 6.0,
    "frijol": 4.5,
    "agave": 2.5,
    "aguacate": 7.0,
    "jitomate": 7.5,
    "calabaza": 5.0,
    "chile": 5.5,
    "sorgo": 4.5,
}
DEFAULT_OPTIMAL_MM = 5.5


class WaterEfficiencyResult(TypedDict):
    field_hectares: float
    crop_type: str
    water_stress_index: float  # 0-1: 0=no stress, 1=critical
    optimal_irrigation_mm: float  # mm/day to apply under current conditions
    liters_wasted: float  # estimated liters wasted per day from over/under scheduling
    recomendacion: str  # Spanish recommendation


def compute_water_efficiency(
    hectares: float,
    crop_type: str | None,
    weather: dict | None,
    thermal: dict | None,
) -> WaterEfficiencyResult:
    """Compute water use efficiency metrics.

    Args:
        hectares: Field size in hectares.
        crop_type: Crop type string (maiz, agave, etc.)
        weather: {temp_c, humidity_pct, recent_rainfall_mm} or None.
        thermal: {stress_pct, irrigation_deficit} or None.

    Returns:
        WaterEfficiencyResult with stress index, optimal mm, and wasted liters.
    """
    temp_c: float = (weather or {}).get("temp_c", 25.0) or 25.0
    humidity_pct: float = (weather or {}).get("humidity_pct", 50.0) or 50.0
    rainfall_mm: float = (weather or {}).get("recent_rainfall_mm", 0.0) or 0.0

    stress_pct: float = (thermal or {}).get("stress_pct", 0.0) or 0.0
    irrigation_deficit: bool = bool((thermal or {}).get("irrigation_deficit", False))

    # --- Compute stress index (0–1) ---
    stress = 0.0

    # Temperature component (0–0.35)
    if temp_c >= 40:
        stress += 0.35
    elif temp_c >= 35:
        stress += 0.25
    elif temp_c >= 30:
        stress += 0.15
    elif temp_c >= 28:
        stress += 0.08

    # Humidity component (0–0.20)
    if humidity_pct <= 20:
        stress += 0.20
    elif humidity_pct <= 35:
        stress += 0.15
    elif humidity_pct <= 50:
        stress += 0.08

    # Rainfall relief (negative, up to -0.30)
    if rainfall_mm >= RAINFALL_FULL_COVERAGE_MM:
        stress -= 0.30
    elif rainfall_mm >= 10:
        stress -= 0.20
    elif rainfall_mm >= 5:
        stress -= 0.10

    # Thermal stress component (0–0.30)
    stress += min(0.30, stress_pct / 100.0 * 0.30)

    # Irrigation deficit flag adds 0.20
    if irrigation_deficit:
        stress += 0.20

    # Clamp to [0, 1]
    stress = round(max(0.0, min(1.0, stress)), 3)

    # --- Optimal irrigation (mm/day) ---
    base_mm = CROP_OPTIMAL_IRRIGATION_MM.get(crop_type or "", DEFAULT_OPTIMAL_MM)

    # Reduce by rainfall
    rain_offset = min(rainfall_mm, RAINFALL_FULL_COVERAGE_MM)
    adjusted_mm = max(0.0, base_mm - (rain_offset / RAINFALL_FULL_COVERAGE_MM) * base_mm)

    # Scale up under heat stress
    if temp_c >= 35 or irrigation_deficit:
        adjusted_mm *= 1.3
    elif temp_c >= 30:
        adjusted_mm *= 1.1

    optimal_mm = round(adjusted_mm, 2)

    # --- Liters wasted per day (over-irrigation under cool/rainy conditions) ---
    # 1mm on 1ha = 10,000 litres
    liters_per_mm_per_ha = 10_000.0

    # Waste estimate: when rainfall covers need but farmer would still irrigate at base rate
    if rainfall_mm >= base_mm and stress < 0.3:
        # Heavy rain — irrigating at base rate wastes proportionally to excess rain
        waste_mm = max(0.0, rainfall_mm - base_mm)
        liters_wasted = waste_mm * liters_per_mm_per_ha * hectares
    elif stress >= 0.7:
        # High stress — under-irrigation waste (opportunity cost)
        under_mm = max(0.0, optimal_mm - base_mm * 0.5)
        liters_wasted = under_mm * liters_per_mm_per_ha * hectares
    else:
        liters_wasted = 0.0

    liters_wasted = round(liters_wasted, 0)

    # --- Spanish recommendation ---
    crop_name = crop_type or "cultivo"
    if stress >= 0.7:
        recomendacion = (
            f"Estres hidrico critico detectado en {crop_name}. "
            f"Aplicar riego de {optimal_mm:.1f} mm/dia. "
            f"Priorizar riego antes de las 8am para reducir evaporacion."
        )
    elif stress >= 0.4:
        recomendacion = (
            f"Estres hidrico moderado. Se recomienda riego de {optimal_mm:.1f} mm/dia "
            f"para {crop_name}. Monitorear temperatura y humedad del suelo."
        )
    elif rainfall_mm >= 10:
        recomendacion = (
            f"Lluvia reciente de {rainfall_mm:.0f} mm reduce la necesidad de riego. "
            f"Evitar irrigar para no desperdiciar agua."
        )
    else:
        recomendacion = (
            f"Condiciones hidricas normales para {crop_name}. "
            f"Riego optimo de {optimal_mm:.1f} mm/dia. "
            f"Mantener monitoreo regular de humedad del suelo."
        )

    return WaterEfficiencyResult(
        field_hectares=hectares,
        crop_type=crop_type or "desconocido",
        water_stress_index=stress,
        optimal_irrigation_mm=optimal_mm,
        liters_wasted=liters_wasted,
        recomendacion=recomendacion,
    )
