"""Active alert summary service.

GET /api/farms/{farm_id}/active-alerts-summary

Composes per-field signals into a farm-level alert summary:
- WeatherRecord → detect_weather_alerts (severity: critica → critical, moderada → high)
- compute_water_stress → urgency: severe → critical, moderate → high
- compute_disease_risk_assessment → risk: high → critical, medium → high

Returns {farm_id, critical_count, high_count, top_action_es, next_check_date, safe}
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from cultivos.db.models import Farm, WeatherRecord
from cultivos.services.intelligence.disease_risk_assessment import compute_disease_risk_assessment
from cultivos.services.intelligence.water_stress import compute_water_stress
from cultivos.services.intelligence.weather_alerts import detect_weather_alerts

_SAFE_ACTION_ES = "Sin alertas activas — continuar monitoreo regular del campo."
_FALLBACK_ACTION_ES = "Revisar las condiciones del campo y aplicar medidas preventivas."

# next_check_date offsets by urgency
_DAYS_CRITICAL = 1
_DAYS_HIGH = 3
_DAYS_SAFE = 7


def compute_active_alerts_summary(farm: Farm, db: Session) -> dict:
    """Return active alert summary for a farm across all fields."""
    critical_count = 0
    high_count = 0
    top_action_es: str | None = None
    top_priority = 0  # 2=critical, 1=high — track highest seen

    fields = farm.fields if farm.fields else []

    # Per-field signal aggregation
    for field in fields:
        # --- Water stress ---
        ws = compute_water_stress(field, db)
        urgency = ws.get("urgency_level", "none")
        if urgency == "severe":
            critical_count += 1
            if top_priority < 2:
                top_priority = 2
                top_action_es = ws.get("recommended_action_es", _FALLBACK_ACTION_ES)
        elif urgency == "moderate":
            high_count += 1
            if top_priority < 1:
                top_priority = 1
                top_action_es = ws.get("recommended_action_es", _FALLBACK_ACTION_ES)

        # --- Disease risk ---
        dr = compute_disease_risk_assessment(field, db)
        risk = dr.get("risk_level", "low")
        if risk == "high":
            critical_count += 1
            if top_priority < 2:
                top_priority = 2
                top_action_es = (
                    "Riesgo de enfermedad alto — inspeccionar el campo y aplicar tratamiento preventivo."
                )
        elif risk == "medium":
            high_count += 1
            if top_priority < 1:
                top_priority = 1
                top_action_es = (
                    "Riesgo de enfermedad moderado — monitorear síntomas y preparar tratamiento orgánico."
                )

    # --- Weather alerts (farm-level, applied to each field) ---
    weather = (
        db.query(WeatherRecord)
        .filter(WeatherRecord.farm_id == farm.id)
        .order_by(WeatherRecord.recorded_at.desc())
        .first()
    )
    if weather is not None:
        alerts = detect_weather_alerts(
            temp_c=weather.temp_c,
            humidity_pct=weather.humidity_pct,
            wind_kmh=weather.wind_kmh,
            rainfall_mm=weather.rainfall_mm,
            description=weather.description,
            forecast_3day=weather.forecast_3day or [],
        )
        for alert in alerts:
            severity = alert.get("severity", "moderada")
            actions = alert.get("actions", [])
            action_text = actions[0] if actions else _FALLBACK_ACTION_ES
            if severity == "critica":
                critical_count += 1
                if top_priority < 2:
                    top_priority = 2
                    top_action_es = action_text
            else:  # moderada
                high_count += 1
                if top_priority < 1:
                    top_priority = 1
                    top_action_es = action_text

    safe = (critical_count + high_count) == 0

    if safe or top_action_es is None:
        top_action_es = _SAFE_ACTION_ES

    # next_check_date
    if critical_count > 0:
        next_check_date = date.today() + timedelta(days=_DAYS_CRITICAL)
    elif high_count > 0:
        next_check_date = date.today() + timedelta(days=_DAYS_HIGH)
    else:
        next_check_date = date.today() + timedelta(days=_DAYS_SAFE)

    return {
        "farm_id": farm.id,
        "critical_count": critical_count,
        "high_count": high_count,
        "top_action_es": top_action_es,
        "next_check_date": next_check_date.isoformat(),
        "safe": safe,
    }
