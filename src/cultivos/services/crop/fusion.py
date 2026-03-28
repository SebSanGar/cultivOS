"""Multi-sensor fusion validation — cross-check NDVI + thermal + soil + weather.

Pure function: sensor data in, validation result out. No HTTP, no DB.
Flags contradictions between sensors and computes a confidence score
based on sensor agreement and data completeness.
"""

from typing import TypedDict

from cultivos.services.crop.health import NDVIInput, ThermalInput, SoilInput


class WeatherInput(TypedDict, total=False):
    temp_c: float
    humidity_pct: float
    wind_kmh: float


class SensorContradiction(TypedDict):
    tag: str  # machine-readable identifier
    sensors: list[str]  # which sensors disagree
    description: str  # Spanish farmer-facing explanation


class FusionResult(TypedDict):
    contradictions: list[SensorContradiction]
    confidence: float  # 0.0-1.0
    sensors_used: list[str]
    assessment: str  # Spanish farmer-facing summary


# --- Sensor base reliability weights (sum to 1.0) ---
_SENSOR_WEIGHTS = {
    "ndvi": 0.35,
    "thermal": 0.25,
    "soil": 0.25,
    "weather": 0.15,
}


def _classify_ndvi(ndvi: NDVIInput) -> str:
    """Classify NDVI as healthy, moderate, or stressed."""
    mean = ndvi.get("ndvi_mean", 0.0)
    stress = ndvi.get("stress_pct", 0.0)
    if mean >= 0.6 and stress < 20:
        return "healthy"
    elif mean >= 0.4 and stress < 40:
        return "moderate"
    return "stressed"


def _classify_thermal(thermal: ThermalInput) -> str:
    """Classify thermal as healthy, moderate, or stressed."""
    stress = thermal.get("stress_pct", 0.0)
    temp = thermal.get("temp_mean", 25.0)
    if stress < 15 and temp < 33:
        return "healthy"
    elif stress < 35 and temp < 37:
        return "moderate"
    return "stressed"


def _classify_soil(soil: SoilInput) -> str:
    """Classify soil as healthy, moderate, or stressed."""
    scores = []
    ph = soil.get("ph")
    if ph is not None:
        scores.append(1.0 if 5.5 <= ph <= 7.5 else 0.0)
    om = soil.get("organic_matter_pct")
    if om is not None:
        scores.append(1.0 if om >= 3.0 else 0.0)
    moisture = soil.get("moisture_pct")
    if moisture is not None:
        scores.append(1.0 if 15 <= moisture <= 65 else 0.0)
    n = soil.get("nitrogen_ppm")
    if n is not None:
        scores.append(1.0 if 15 <= n <= 70 else 0.0)
    if not scores:
        return "moderate"
    avg = sum(scores) / len(scores)
    if avg >= 0.7:
        return "healthy"
    elif avg >= 0.4:
        return "moderate"
    return "stressed"


def _classify_weather(weather: WeatherInput) -> str:
    """Classify weather as favorable, moderate, or harsh."""
    temp = weather.get("temp_c", 25.0)
    humidity = weather.get("humidity_pct", 50)
    if temp > 38 or temp < 5 or humidity < 15:
        return "harsh"
    elif temp > 33 or humidity < 25:
        return "moderate"
    return "favorable"


def _detect_contradictions(
    classifications: dict[str, str],
    ndvi: NDVIInput | None,
    thermal: ThermalInput | None,
    soil: SoilInput | None,
    weather: WeatherInput | None,
) -> list[SensorContradiction]:
    """Detect contradictions between sensor readings."""
    contradictions: list[SensorContradiction] = []

    # NDVI healthy but thermal stressed
    if (
        classifications.get("ndvi") == "healthy"
        and classifications.get("thermal") == "stressed"
    ):
        contradictions.append(
            SensorContradiction(
                tag="ndvi_thermal_mismatch",
                sensors=["ndvi", "thermal"],
                description=(
                    "El NDVI indica vegetacion sana pero el sensor termico "
                    "detecta estres por calor. Posible problema de riego o "
                    "estres radicular no visible en superficie."
                ),
            )
        )

    # NDVI stressed but soil healthy
    if (
        classifications.get("ndvi") == "stressed"
        and classifications.get("soil") == "healthy"
    ):
        contradictions.append(
            SensorContradiction(
                tag="ndvi_soil_mismatch",
                sensors=["ndvi", "soil"],
                description=(
                    "El NDVI muestra estres pero el suelo esta en buenas condiciones. "
                    "Posible plaga, enfermedad foliar, o dano mecanico."
                ),
            )
        )

    # Weather hot but thermal cool
    if (
        classifications.get("weather") in ("harsh",)
        and weather is not None
        and weather.get("temp_c", 25.0) > 35
        and classifications.get("thermal") == "healthy"
    ):
        contradictions.append(
            SensorContradiction(
                tag="weather_thermal_mismatch",
                sensors=["weather", "thermal"],
                description=(
                    "El clima reporta temperaturas altas pero el sensor termico "
                    "no detecta estres. Verificar calibracion del sensor termico "
                    "o desfase temporal entre lecturas."
                ),
            )
        )

    # Thermal stressed but soil moisture high (overwatering vs stress)
    if (
        classifications.get("thermal") == "stressed"
        and soil is not None
        and (soil.get("moisture_pct") or 0) > 50
    ):
        contradictions.append(
            SensorContradiction(
                tag="thermal_soil_moisture_mismatch",
                sensors=["thermal", "soil"],
                description=(
                    "El sensor termico muestra estres pero el suelo tiene humedad alta. "
                    "Posible encharcamiento o problema radicular."
                ),
            )
        )

    return contradictions


def _compute_confidence(
    sensors_used: list[str],
    contradictions: list[SensorContradiction],
) -> float:
    """Compute confidence 0.0-1.0 based on sensor coverage and agreement.

    Base confidence from sensor coverage (more sensors = higher base).
    Contradictions reduce confidence.
    """
    if not sensors_used:
        return 0.0

    # Base: weighted sum of available sensors
    total_weight = sum(_SENSOR_WEIGHTS.get(s, 0.0) for s in sensors_used)
    # Scale so 4 sensors = 0.9 base, 1 sensor = ~0.3
    base = min(0.9, total_weight * 0.9)

    # Penalty per contradiction: -0.15
    penalty = len(contradictions) * 0.15

    return max(0.0, min(1.0, round(base - penalty, 2)))


def _generate_assessment(
    sensors_used: list[str],
    classifications: dict[str, str],
    contradictions: list[SensorContradiction],
    confidence: float,
) -> str:
    """Generate farmer-facing Spanish assessment."""
    n = len(sensors_used)

    if contradictions:
        issues = "; ".join(c["description"] for c in contradictions)
        return (
            f"Se detectaron {len(contradictions)} inconsistencia(s) entre sensores. "
            f"{issues} "
            f"Confianza: {confidence:.0%} (basada en {n} sensor(es))."
        )

    # All consistent
    states = [classifications[s] for s in sensors_used if s in classifications]
    if all(s in ("healthy", "favorable") for s in states):
        return (
            f"Todos los {n} sensores coinciden: campo en buen estado. "
            f"Confianza: {confidence:.0%}."
        )
    elif any(s == "stressed" or s == "harsh" for s in states):
        return (
            f"Los {n} sensores coinciden en detectar estres. "
            f"Se recomienda accion inmediata. Confianza: {confidence:.0%}."
        )
    return (
        f"Condiciones moderadas segun {n} sensor(es). "
        f"Confianza: {confidence:.0%}."
    )


def validate_sensor_fusion(
    ndvi: NDVIInput | None = None,
    thermal: ThermalInput | None = None,
    soil: SoilInput | None = None,
    weather: WeatherInput | None = None,
) -> FusionResult:
    """Cross-validate multiple sensor readings for a field.

    Flags contradictions (e.g. NDVI healthy but thermal stressed),
    computes confidence based on sensor coverage and agreement,
    and returns a farmer-facing Spanish assessment.

    All inputs are optional — works with partial data.
    """
    sensors_used: list[str] = []
    classifications: dict[str, str] = {}

    if ndvi is not None:
        sensors_used.append("ndvi")
        classifications["ndvi"] = _classify_ndvi(ndvi)

    if thermal is not None:
        sensors_used.append("thermal")
        classifications["thermal"] = _classify_thermal(thermal)

    if soil is not None:
        sensors_used.append("soil")
        classifications["soil"] = _classify_soil(soil)

    if weather is not None:
        sensors_used.append("weather")
        classifications["weather"] = _classify_weather(weather)

    contradictions = _detect_contradictions(
        classifications, ndvi, thermal, soil, weather
    )

    confidence = _compute_confidence(sensors_used, contradictions)

    assessment = _generate_assessment(
        sensors_used, classifications, contradictions, confidence
    )

    return FusionResult(
        contradictions=contradictions,
        confidence=confidence,
        sensors_used=sensors_used,
        assessment=assessment,
    )
