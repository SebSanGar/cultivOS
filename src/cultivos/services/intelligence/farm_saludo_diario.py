"""Farm daily Spanish greeting — composes weather + field urgency + alert count."""

from sqlalchemy.orm import Session

from cultivos.db.models import AlertLog, Farm, Field, WeatherRecord
from cultivos.services.intelligence.field_accion import compute_field_accion

_PRIORITY_RANK = {"alta": 3, "media": 2, "baja": 1, "ninguna": 0}


def _weather_sentence(farm_id: int, db: Session) -> str:
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

    return f"Hoy {temp_desc}, {temp}°C, {hum}% humedad."


def compute_saludo_diario(farm: Farm, db: Session) -> dict:
    open_alerts = (
        db.query(AlertLog)
        .filter(AlertLog.farm_id == farm.id, AlertLog.acknowledged == False)
        .count()
    )

    fields = db.query(Field).filter(Field.farm_id == farm.id).all()
    urgent_field = None
    if fields:
        acciones = [compute_field_accion(f, db) for f in fields]
        acciones.sort(
            key=lambda a: _PRIORITY_RANK.get(a["priority"], 0), reverse=True
        )
        top = acciones[0]
        if top["priority"] != "ninguna":
            urgent_field = top["field_name"]

    weather_es = _weather_sentence(farm.id, db)

    if open_alerts == 0 and urgent_field is None:
        saludo = f"Buenos días, {farm.name}. {weather_es} Todo tranquilo, buen día para monitoreo."
    elif urgent_field:
        saludo = f"Buenos días, {farm.name}. {weather_es} {open_alerts} alerta(s) abierta(s), prioridad: {urgent_field}."
    else:
        saludo = f"Buenos días, {farm.name}. {weather_es} {open_alerts} alerta(s) abierta(s)."

    if len(saludo) > 200:
        saludo = saludo[:197] + "..."

    return {
        "farm_name": farm.name,
        "weather_es": weather_es,
        "open_alerts": open_alerts,
        "urgent_field": urgent_field,
        "saludo_es": saludo,
    }
