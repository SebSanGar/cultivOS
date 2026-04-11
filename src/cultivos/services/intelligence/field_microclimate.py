"""Field micro-climate summary service.

Aggregates last 7 days of WeatherRecord for the field's farm.
Returns temp stats, rainfall, humidity, wind, and frost risk count.
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from cultivos.db.models import Field, WeatherRecord

_PERIOD_DAYS = 7
_FROST_THRESHOLD_C = 4.0


def _build_summary_es(
    avg_temp: float | None,
    total_rain: float,
    frost_days: int,
) -> str:
    if avg_temp is None:
        return "Sin datos climaticos disponibles para los ultimos 7 dias."

    parts = []
    if avg_temp >= 25:
        parts.append("Clima calido")
    elif avg_temp >= 15:
        parts.append("Clima templado")
    else:
        parts.append("Clima frio")

    if total_rain >= 10:
        parts.append(f"con lluvias significativas ({total_rain:.1f} mm)")
    elif total_rain > 0:
        parts.append(f"con lluvias ligeras ({total_rain:.1f} mm)")
    else:
        parts.append("sin precipitaciones")

    if frost_days > 0:
        parts.append(f"y riesgo de helada {frost_days} dia{'s' if frost_days != 1 else ''}")

    return ", ".join(parts) + "."


def compute_field_microclimate(field: Field, db: Session) -> dict:
    """Aggregate last 7 days of weather for the field's farm."""
    cutoff = datetime.utcnow() - timedelta(days=_PERIOD_DAYS)

    records = (
        db.query(WeatherRecord)
        .filter(
            WeatherRecord.farm_id == field.farm_id,
            WeatherRecord.recorded_at >= cutoff,
        )
        .all()
    )

    if not records:
        return {
            "field_id": field.id,
            "period_days": _PERIOD_DAYS,
            "avg_temp_c": None,
            "max_temp_c": None,
            "min_temp_c": None,
            "total_rainfall_mm": 0.0,
            "avg_humidity_pct": None,
            "avg_wind_speed_kmh": None,
            "frost_risk_days": 0,
            "summary_es": _build_summary_es(None, 0.0, 0),
        }

    temps = [r.temp_c for r in records]
    avg_temp = round(sum(temps) / len(temps), 1)
    max_temp = round(max(temps), 1)
    min_temp = round(min(temps), 1)

    total_rain = round(sum(r.rainfall_mm for r in records), 1)

    humidities = [r.humidity_pct for r in records]
    avg_humidity = round(sum(humidities) / len(humidities), 1)

    winds = [r.wind_kmh for r in records]
    avg_wind = round(sum(winds) / len(winds), 1)

    frost_days = sum(1 for r in records if r.temp_c < _FROST_THRESHOLD_C)

    return {
        "field_id": field.id,
        "period_days": _PERIOD_DAYS,
        "avg_temp_c": avg_temp,
        "max_temp_c": max_temp,
        "min_temp_c": min_temp,
        "total_rainfall_mm": total_rain,
        "avg_humidity_pct": avg_humidity,
        "avg_wind_speed_kmh": avg_wind,
        "frost_risk_days": frost_days,
        "summary_es": _build_summary_es(avg_temp, total_rain, frost_days),
    }
