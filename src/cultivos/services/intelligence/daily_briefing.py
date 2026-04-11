"""Daily briefing service — composes field priority + weather + upcoming treatments.

Produces a concise, voice-friendly daily action summary for a farm in Spanish.

Logic:
  overall_farm_status:
    urgent    if any field priority_score >= 60
    attention if any field priority_score >= 30
    ok        otherwise (or no fields)
  weather_summary_es: Spanish sentence from latest WeatherRecord (temp + humidity)
  urgent_field: top-ranked field (highest priority_score) if status != ok
  upcoming_treatments: first upcoming treatment per field (soonest)
"""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, WeatherRecord
from cultivos.services.intelligence.field_priority import compute_field_priority
from cultivos.services.intelligence.upcoming_treatments import compute_upcoming_treatments


# Thresholds that determine overall farm status
_URGENT_THRESHOLD = 60.0
_ATTENTION_THRESHOLD = 30.0


def _weather_summary(farm_id: int, db: Session) -> str:
    """Return a Spanish weather sentence or graceful fallback."""
    weather = (
        db.query(WeatherRecord)
        .filter(WeatherRecord.farm_id == farm_id)
        .order_by(WeatherRecord.recorded_at.desc())
        .first()
    )
    if weather is None:
        return "Sin datos meteorológicos disponibles."

    temp = round(weather.temp_c)
    hum = round(weather.humidity_pct)

    if temp >= 35:
        temp_desc = "muy caluroso"
    elif temp >= 28:
        temp_desc = "caluroso"
    elif temp >= 18:
        temp_desc = "templado"
    else:
        temp_desc = "fresco"

    if hum >= 80:
        hum_desc = "humedad muy alta — riesgo de hongos"
    elif hum >= 60:
        hum_desc = "humedad moderada"
    else:
        hum_desc = "ambiente seco"

    return f"Hoy {temp_desc}, {temp}°C con {hum}% de humedad ({hum_desc})."


def compute_daily_briefing(farm: Farm, db: Session) -> dict:
    """Compute the daily farm briefing.

    Returns a dict with keys:
        date, weather_summary_es, urgent_field, upcoming_treatments, overall_farm_status
    """
    # --- Field priority ranking ---
    priority_result = compute_field_priority(farm, db)
    ranked_fields: list[dict] = priority_result["fields"]

    # --- Overall farm status ---
    overall_status = "ok"
    for f in ranked_fields:
        score = f["priority_score"]
        if score >= _URGENT_THRESHOLD:
            overall_status = "urgent"
            break
        if score >= _ATTENTION_THRESHOLD:
            overall_status = "attention"

    # --- Urgent field (top ranked, only if status != ok) ---
    urgent_field = None
    if ranked_fields and overall_status != "ok":
        top = ranked_fields[0]
        urgent_field = {
            "name": top["name"],
            "issue_es": top["top_issue"],
            "action_es": top["recommended_action"],
        }

    # --- Upcoming treatment reminders (one per field, soonest window) ---
    fields: list[Field] = (
        db.query(Field).filter(Field.farm_id == farm.id).all()
    )
    upcoming_treatments: list[dict] = []
    for field in fields:
        treatments = compute_upcoming_treatments(field, db)
        if treatments:
            first = treatments[0]
            upcoming_treatments.append({
                "field_name": field.name,
                "treatment": first.treatment_type,
                "due_date": first.recommended_date,
            })

    # --- Weather summary ---
    weather_summary = _weather_summary(farm.id, db)

    return {
        "date": date.today().isoformat(),
        "weather_summary_es": weather_summary,
        "urgent_field": urgent_field,
        "upcoming_treatments": upcoming_treatments,
        "overall_farm_status": overall_status,
    }
