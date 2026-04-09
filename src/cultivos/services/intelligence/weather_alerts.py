"""Weather alert detection — pure function, no I/O.

Checks current weather and forecast against severity thresholds.
Returns a list of warning dicts with type, severity, message, and
protective action recommendations in Spanish.
"""

from __future__ import annotations


# Thresholds for severe weather conditions
FROST_TEMP_C = 2.0
EXTREME_HEAT_C = 38.0
HEAVY_RAIN_MM = 50.0
HIGH_WIND_KMH = 60.0
HAIL_INDICATORS = {"granizo", "hail", "pedrisco"}


def _classify_severity(value: float, warning_threshold: float, critical_threshold: float) -> str:
    """Return 'critica' or 'moderada' based on how far past the threshold."""
    if abs(value) >= abs(critical_threshold):
        return "critica"
    return "moderada"


def detect_weather_alerts(
    temp_c: float,
    humidity_pct: float,
    wind_kmh: float,
    rainfall_mm: float,
    description: str = "",
    forecast_3day: list[dict] | None = None,
) -> list[dict]:
    """Detect severe weather conditions from current + forecast data.

    Returns list of dicts, each with:
        - alert_type: frost | extreme_heat | heavy_rain | high_wind | hail
        - severity: critica | moderada
        - title: short Spanish title
        - message: detailed Spanish description
        - actions: list of protective action recommendations (Spanish)
        - source: "current" | "forecast_day_N"
    """
    alerts: list[dict] = []

    # --- Current conditions ---
    _check_conditions(
        temp_c=temp_c,
        humidity_pct=humidity_pct,
        wind_kmh=wind_kmh,
        rainfall_mm=rainfall_mm,
        description=description,
        source="current",
        alerts=alerts,
    )

    # --- Forecast conditions ---
    if forecast_3day:
        for i, day in enumerate(forecast_3day):
            _check_conditions(
                temp_c=day.get("temp_c", 20.0),
                humidity_pct=day.get("humidity_pct", 50.0),
                wind_kmh=day.get("wind_kmh", 0.0),
                rainfall_mm=day.get("rainfall_mm", 0.0),
                description=day.get("description", ""),
                source=f"forecast_day_{i + 1}",
                alerts=alerts,
            )

    return alerts


def _check_conditions(
    *,
    temp_c: float,
    humidity_pct: float,
    wind_kmh: float,
    rainfall_mm: float,
    description: str,
    source: str,
    alerts: list[dict],
) -> None:
    """Check a single set of weather conditions against all thresholds."""

    # Frost
    if temp_c <= FROST_TEMP_C:
        severity = "critica" if temp_c <= 0.0 else "moderada"
        alerts.append({
            "alert_type": "frost",
            "severity": severity,
            "title": "Helada" if severity == "critica" else "Riesgo de helada",
            "message": f"Temperatura de {temp_c:.1f}C detectada — riesgo de dano por helada en cultivos sensibles.",
            "actions": [
                "Cubrir cultivos sensibles con manta termica o plastico",
                "Regar por aspersion antes del amanecer para proteger con capa de hielo",
                "Aplicar mulch organico alrededor de la base de las plantas",
                "Cosechar cultivos maduros antes de la helada si es posible",
            ],
            "source": source,
        })

    # Extreme heat
    if temp_c >= EXTREME_HEAT_C:
        severity = "critica" if temp_c >= 42.0 else "moderada"
        alerts.append({
            "alert_type": "extreme_heat",
            "severity": severity,
            "title": "Calor extremo",
            "message": f"Temperatura de {temp_c:.1f}C — riesgo de estres termico y deshidratacion en cultivos.",
            "actions": [
                "Aumentar frecuencia de riego — regar temprano en la manana o al atardecer",
                "Aplicar mulch organico para retener humedad del suelo",
                "Instalar malla sombra en cultivos sensibles",
                "Evitar labores de campo en horas pico de calor (12-16h)",
            ],
            "source": source,
        })

    # Heavy rain
    if rainfall_mm >= HEAVY_RAIN_MM:
        severity = "critica" if rainfall_mm >= 80.0 else "moderada"
        alerts.append({
            "alert_type": "heavy_rain",
            "severity": severity,
            "title": "Lluvia intensa",
            "message": f"Precipitacion de {rainfall_mm:.1f}mm — riesgo de inundacion y erosion.",
            "actions": [
                "Verificar canales de drenaje y despejar obstrucciones",
                "Proteger cultivos bajos con barreras de contencion",
                "Posponer aplicacion de fertilizantes organicos — seran lavados",
                "Revisar campos despues de la lluvia para detectar erosion",
            ],
            "source": source,
        })

    # High wind
    if wind_kmh >= HIGH_WIND_KMH:
        severity = "critica" if wind_kmh >= 80.0 else "moderada"
        alerts.append({
            "alert_type": "high_wind",
            "severity": severity,
            "title": "Viento fuerte",
            "message": f"Viento de {wind_kmh:.1f} km/h — riesgo de dano mecanico en cultivos altos.",
            "actions": [
                "Asegurar tutores y estructuras de soporte en cultivos altos",
                "No realizar vuelos de dron — viento excede limites operativos",
                "Proteger invernaderos y mallas sombra",
                "Cosechar frutos maduros antes del evento de viento",
            ],
            "source": source,
        })

    # Hail (from description keywords)
    desc_lower = description.lower()
    if any(kw in desc_lower for kw in HAIL_INDICATORS):
        alerts.append({
            "alert_type": "hail",
            "severity": "critica",
            "title": "Granizo",
            "message": "Se pronostica granizo — riesgo severo de dano fisico en cultivos y frutos.",
            "actions": [
                "Cubrir cultivos con malla antigranizo si esta disponible",
                "Cosechar frutos maduros inmediatamente",
                "Proteger equipos y drones bajo techo",
                "Documentar dano despues del evento para reclamacion de seguro",
            ],
            "source": source,
        })
