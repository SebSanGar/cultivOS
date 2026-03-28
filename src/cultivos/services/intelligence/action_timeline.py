"""Weather-integrated action timeline — unified 7-day action list.

Composes: seasonal calendar + growth stage + weather forecast + pending treatments
into a single prioritized action list. Pure function: data in, timeline out.
"""

from datetime import date, datetime, timedelta
from typing import Any

from cultivos.services.intelligence.seasonal_calendar import generate_seasonal_alerts
from cultivos.services.crop.phenology import compute_growth_stage


# Priority mapping: lower number = higher priority
_URGENCIA_PRIORITY = {"alta": 1, "media": 2, "baja": 3}
_SOURCE_PRIORITY = {"treatment": 1, "growth_stage": 2, "seasonal_calendar": 3}


def _rain_days(forecast_3day: list[dict]) -> list[int]:
    """Return 0-indexed day numbers with significant rain (>5mm)."""
    return [i for i, day in enumerate(forecast_3day) if day.get("rainfall_mm", 0) > 5.0]


def _weather_note_for_treatment(forecast_3day: list[dict]) -> str | None:
    """Generate a weather warning for foliar/spray treatments if rain is forecast."""
    rainy = _rain_days(forecast_3day)
    if not rainy:
        return None
    day_labels = {0: "hoy", 1: "manana", 2: "pasado manana"}
    rain_days_str = ", ".join(day_labels.get(d, f"dia {d+1}") for d in rainy)
    return f"Precaucion: lluvia pronosticada ({rain_days_str}). Considerar reprogramar aplicaciones foliares."


def _weather_summary(forecast_3day: list[dict]) -> dict | None:
    """Build a brief weather summary from 3-day forecast."""
    if not forecast_3day:
        return None
    total_rain = sum(d.get("rainfall_mm", 0) for d in forecast_3day)
    max_temp = max(d.get("temp_c", 0) for d in forecast_3day)
    min_temp = min(d.get("temp_c", 0) for d in forecast_3day)
    rainy_days = len(_rain_days(forecast_3day))
    return {
        "total_rainfall_mm": round(total_rain, 1),
        "max_temp_c": round(max_temp, 1),
        "min_temp_c": round(min_temp, 1),
        "rainy_days": rainy_days,
        "forecast_days": len(forecast_3day),
    }


def build_action_timeline(
    reference_date: date | None = None,
    crop_type: str | None = None,
    planted_at: datetime | None = None,
    forecast_3day: list[dict] | None = None,
    pending_treatments: list[dict] | None = None,
) -> dict[str, Any]:
    """Build a unified action timeline for the next 7 days.

    Combines four data sources into a single prioritized list:
    1. Seasonal TEK calendar alerts (month-based)
    2. Growth stage actions (from planted_at + crop_type)
    3. Weather-influenced treatment scheduling
    4. Pending (unapplied) treatments

    Args:
        reference_date: Date to generate timeline for (defaults to today).
        crop_type: Crop type for this field (e.g. "maiz").
        planted_at: When the crop was planted.
        forecast_3day: List of forecast day dicts with temp_c, rainfall_mm, etc.
        pending_treatments: List of pending treatment dicts (id, problema, tratamiento, urgencia, etc.)

    Returns:
        Dict with actions list sorted by priority, weather_summary, and metadata.
    """
    if reference_date is None:
        reference_date = date.today()
    forecast_3day = forecast_3day or []
    pending_treatments = pending_treatments or []

    actions: list[dict[str, Any]] = []

    # 1. Seasonal calendar alerts
    seasonal = generate_seasonal_alerts(reference_date)
    if crop_type:
        # Filter to this field's crop + general alerts
        crop_lower = crop_type.lower()
        seasonal = [a for a in seasonal if a["crop"].lower() == crop_lower or a["crop"].lower() == "milpa"]
    for alert in seasonal:
        actions.append({
            "source": "seasonal_calendar",
            "priority": _SOURCE_PRIORITY["seasonal_calendar"],
            "crop": alert["crop"],
            "action_type": alert["alert_type"],
            "description": alert["message"],
            "season": alert["season"],
            "month_range": alert["month_range"],
            "weather_note": None,
        })

    # 2. Growth stage actions
    if crop_type and planted_at:
        ref_dt = datetime(reference_date.year, reference_date.month, reference_date.day)
        stage = compute_growth_stage(crop_type, planted_at, ref_dt)
        if stage:
            actions.append({
                "source": "growth_stage",
                "priority": _SOURCE_PRIORITY["growth_stage"],
                "stage": stage["stage"],
                "stage_es": stage["stage_es"],
                "action_type": "cuidado",
                "description": stage["nutrient_focus"],
                "days_in_stage": stage["days_in_stage"],
                "days_until_next_stage": stage["days_until_next_stage"],
                "water_multiplier": stage["water_multiplier"],
                "weather_note": None,
            })

    # 3. Pending treatments with weather awareness
    weather_note = _weather_note_for_treatment(forecast_3day)
    for t in pending_treatments:
        urgencia = t.get("urgencia", "media")
        actions.append({
            "source": "treatment",
            "priority": _URGENCIA_PRIORITY.get(urgencia, 2),
            "treatment_id": t.get("id"),
            "action_type": "tratamiento",
            "description": t.get("tratamiento", ""),
            "problema": t.get("problema", ""),
            "urgencia": urgencia,
            "costo_estimado_mxn": t.get("costo_estimado_mxn", 0),
            "weather_note": weather_note,
        })

    # Sort by priority (lower = more urgent)
    actions.sort(key=lambda a: a["priority"])

    return {
        "reference_date": reference_date.isoformat(),
        "crop_type": crop_type,
        "action_count": len(actions),
        "weather_summary": _weather_summary(forecast_3day),
        "actions": actions,
    }
