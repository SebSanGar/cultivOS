"""Water stress early warning service — irrigation urgency from multi-sensor data.

Combines:
  - Soil moisture (SoilAnalysis.moisture_pct) — latest record
  - Thermal stress (ThermalResult.stress_pct / irrigation_deficit) — latest record
  - Weather temperature (WeatherRecord.temp_c) — latest farm-level record

Urgency levels:
  severe   — 3 factors OR (soil < 20% AND temp > 35°C)
  moderate — 2 factors OR soil < 20%
  low      — 1 factor
  none     — 0 factors

Graceful degradation: missing soil → use thermal + weather only.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from cultivos.db.models import Field, SoilAnalysis, ThermalResult, WeatherRecord


# Thresholds
_SOIL_CRITICAL = 20.0   # < 20% → extreme dryness
_SOIL_LOW = 30.0        # < 30% → low moisture
_THERMAL_STRESS_PCT = 40.0  # >= 40% stress_pct → thermal stressed
_TEMP_HOT = 35.0        # > 35°C → hot day


_ACTIONS: dict[str, str] = {
    "severe": (
        "Riego urgente requerido — aplicar agua de inmediato para evitar pérdida de cosecha. "
        "Revisar el campo hoy."
    ),
    "moderate": (
        "Programar riego en las próximas 24 horas. Monitorear humedad del suelo y temperatura."
    ),
    "low": (
        "Monitoreo recomendado — verificar humedad del suelo antes del próximo riego programado."
    ),
    "none": (
        "Sin estrés hídrico detectado — mantener el calendario de riego habitual."
    ),
}

_NEXT_CHECK: dict[str, int] = {
    "severe": 4,
    "moderate": 12,
    "low": 24,
    "none": 48,
}


def compute_water_stress(field: Field, db: Session) -> dict:
    """Assess water stress urgency for a field.

    Returns a dict with keys:
        urgency_level, contributing_factors, recommended_action_es, next_check_hours
    """
    factors: list[str] = []
    soil_critical = False  # moisture < 20%

    # --- Soil moisture ---
    soil = (
        db.query(SoilAnalysis)
        .filter(SoilAnalysis.field_id == field.id)
        .order_by(SoilAnalysis.created_at.desc())
        .first()
    )
    if soil is not None and soil.moisture_pct is not None:
        if soil.moisture_pct < _SOIL_CRITICAL:
            factors.append(f"Humedad del suelo crítica ({soil.moisture_pct:.0f}% < 20%)")
            soil_critical = True
        elif soil.moisture_pct < _SOIL_LOW:
            factors.append(f"Humedad del suelo baja ({soil.moisture_pct:.0f}% < 30%)")

    # --- Thermal stress ---
    thermal = (
        db.query(ThermalResult)
        .filter(ThermalResult.field_id == field.id)
        .order_by(ThermalResult.analyzed_at.desc())
        .first()
    )
    if thermal is not None:
        thermal_stressed = thermal.irrigation_deficit or (thermal.stress_pct >= _THERMAL_STRESS_PCT)
        if thermal_stressed:
            if thermal.irrigation_deficit:
                factors.append("Déficit de riego detectado por imagen térmica")
            else:
                factors.append(f"Estrés térmico elevado ({thermal.stress_pct:.0f}% de píxeles afectados)")

    # --- Weather temperature ---
    weather = (
        db.query(WeatherRecord)
        .filter(WeatherRecord.farm_id == field.farm_id)
        .order_by(WeatherRecord.recorded_at.desc())
        .first()
    )
    temp_hot = False
    if weather is not None and weather.temp_c > _TEMP_HOT:
        factors.append(f"Temperatura alta ({weather.temp_c:.0f}°C > 35°C)")
        temp_hot = True

    # --- Urgency classification ---
    factor_count = len(factors)
    if factor_count >= 3 or (soil_critical and temp_hot):
        urgency = "severe"
    elif factor_count >= 2 or soil_critical:
        urgency = "moderate"
    elif factor_count == 1:
        urgency = "low"
    else:
        urgency = "none"

    return {
        "urgency_level": urgency,
        "contributing_factors": factors,
        "recommended_action_es": _ACTIONS[urgency],
        "next_check_hours": _NEXT_CHECK[urgency],
    }
