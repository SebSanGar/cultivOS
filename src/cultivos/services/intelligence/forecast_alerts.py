"""Predictive risk alert service — 3-day weather-driven forecast.

Composes disease risk assessment + current health score + weather to project
risk level 3 days ahead. Designed for FODECIJAL demo: "system warns 3 days
before a problem manifests."

Projection rules:
  high:   disease risk_score >= 50 OR (health_score < 40 AND humidity > 70%)
  medium: disease risk_score >= 25 OR health_score < 60 OR humidity > 60%
  low:    default
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from cultivos.db.models import Field, HealthScore, WeatherRecord
from cultivos.services.intelligence.disease_risk_assessment import (
    compute_disease_risk_assessment,
)


# Risk thresholds
_HIGH_DISEASE_SCORE = 50.0
_MEDIUM_DISEASE_SCORE = 25.0
_HIGH_HUMIDITY = 70.0       # % — disease outbreak risk
_MEDIUM_HUMIDITY = 60.0     # %
_LOW_HEALTH = 40.0          # score — critical
_MEDIUM_HEALTH = 60.0       # score


_PREVENTIVE_ACTIONS: dict[str, list[str]] = {
    "high": [
        "Aplicar fungicida orgánico (caldo bordelés o extracto de ajo) inmediatamente.",
        "Mejorar la ventilación entre plantas — evitar encharcamiento foliar.",
        "Revisar el campo en las próximas 24 horas y documentar síntomas.",
    ],
    "medium": [
        "Monitorear el cultivo cada 48 horas para detectar síntomas tempranos.",
        "Aplicar abono foliar con silicio para fortalecer resistencia.",
        "Evitar riego por aspersión si la humedad supera el 60%.",
    ],
    "low": [
        "Mantener el calendario de monitoreo regular.",
    ],
}


def compute_forecast_alerts(field: Field, db: Session) -> dict:
    """Project risk level 3 days ahead for a field.

    Returns a dict with keys:
        field_id, forecast_date, projected_risk_level, risk_drivers,
        preventive_actions_es
    """
    risk_drivers: list[str] = []

    # --- Disease risk assessment (existing service) ---
    disease = compute_disease_risk_assessment(field, db)
    disease_score: float = disease.get("risk_score", 0.0)

    # --- Latest health score ---
    health_row = (
        db.query(HealthScore)
        .filter(HealthScore.field_id == field.id)
        .order_by(HealthScore.scored_at.desc())
        .first()
    )
    health_score: float | None = health_row.score if health_row else None

    # --- Latest weather (farm-level) ---
    weather = (
        db.query(WeatherRecord)
        .filter(WeatherRecord.farm_id == field.farm_id)
        .order_by(WeatherRecord.recorded_at.desc())
        .first()
    )
    humidity: float | None = weather.humidity_pct if weather else None

    # --- Build risk driver list ---
    if disease_score >= _HIGH_DISEASE_SCORE:
        risk_drivers.append(
            f"Riesgo de enfermedad elevado ({disease_score:.0f}/100) — condiciones favorables "
            "para hongos y plagas en las próximas 72 horas."
        )
    elif disease_score >= _MEDIUM_DISEASE_SCORE:
        risk_drivers.append(
            f"Riesgo de enfermedad moderado ({disease_score:.0f}/100) — vigilancia recomendada."
        )

    if health_score is not None and health_score < _LOW_HEALTH:
        risk_drivers.append(
            f"Salud del cultivo crítica ({health_score:.0f}/100) — planta más vulnerable a enfermedades."
        )
    elif health_score is not None and health_score < _MEDIUM_HEALTH:
        risk_drivers.append(
            f"Salud del cultivo baja ({health_score:.0f}/100) — mayor susceptibilidad a estrés."
        )

    if humidity is not None and humidity > _HIGH_HUMIDITY:
        risk_drivers.append(
            f"Humedad alta ({humidity:.0f}%) — condiciones óptimas para proliferación de hongos."
        )
    elif humidity is not None and humidity > _MEDIUM_HUMIDITY:
        risk_drivers.append(
            f"Humedad moderada-alta ({humidity:.0f}%) — monitorear síntomas foliares."
        )

    # --- Classify projected risk ---
    high_conditions = (
        disease_score >= _HIGH_DISEASE_SCORE
        or (health_score is not None and health_score < _LOW_HEALTH and humidity is not None and humidity > _HIGH_HUMIDITY)
    )
    medium_conditions = (
        disease_score >= _MEDIUM_DISEASE_SCORE
        or (health_score is not None and health_score < _MEDIUM_HEALTH)
        or (humidity is not None and humidity > _MEDIUM_HUMIDITY)
    )

    if high_conditions:
        level = "high"
    elif medium_conditions:
        level = "medium"
    else:
        level = "low"

    return {
        "field_id": field.id,
        "forecast_date": (date.today() + timedelta(days=3)).isoformat(),
        "projected_risk_level": level,
        "risk_drivers": risk_drivers,
        "preventive_actions_es": _PREVENTIVE_ACTIONS[level],
    }
