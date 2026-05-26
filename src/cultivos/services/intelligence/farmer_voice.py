"""Farmer voice translator — maps technical signals to plain Spanish.

Pure function: no I/O, no DB, no HTTP.

translate_to_farmer(signal: dict) -> str

Covers 12 signal types emitted by cultivOS intelligence services.
Output rules:
- One sentence, plain Mexican Spanish
- No technical jargon: no NDVI, ROI, KPI, threshold, optimization,
  anomaly, dashboard, metricas, celsius, pct
- No decimals
- Second-person familiar (tu/te)
"""

from __future__ import annotations

_FALLBACK = "Revisa tu parcela hoy, hay algo que necesita tu atención."


def translate_to_farmer(signal: dict) -> str:
    """Return a plain-Spanish sentence for the given raw signal dict.

    Parameters
    ----------
    signal:
        Dict with at least a ``type`` key. May include numeric keys like
        ``value``, ``celsius``, ``score``, ``drop_pct``, ``rainfall_mm``.

    Returns
    -------
    str
        One-sentence farmer-friendly Spanish description.
    """
    signal_type = signal.get("type", "")
    handler = _HANDLERS.get(signal_type, _handle_unknown)
    return handler(signal)


# ---------------------------------------------------------------------------
# Signal handlers — one per type
# ---------------------------------------------------------------------------

def _handle_low_ndvi(signal: dict) -> str:
    """Low vegetation index → water stress language."""
    return "Tu aguacate tiene sed — dale agua antes de que se seque más."


def _handle_high_thermal(signal: dict) -> str:
    """High thermal reading → heat stress language."""
    return "Hace mucho calor en esa parcela — riega temprano mañana para refrescar las raíces."


def _handle_low_health(signal: dict) -> str:
    """Low health score → general care language."""
    score = signal.get("score")
    if score is not None and int(score) < 40:
        return "Tu parcela no está bien — necesita atención urgente esta semana."
    return "Tu parcela necesita cuidado — revísala pronto para que no empeore."


def _handle_irrigation(signal: dict) -> str:
    """Irrigation trigger → water now language."""
    return "Tu parcela necesita agua — programa el riego hoy."


def _handle_anomaly_health_drop(signal: dict) -> str:
    """Sudden health score drop."""
    return "La salud de tu parcela bajó de golpe — algo cambió, ve a revisar."


def _handle_anomaly_ndvi_drop(signal: dict) -> str:
    """Sudden NDVI drop → plant vigor loss."""
    return "Tus plantas están perdiendo fuerza rápido — revisa si les falta agua o hay plaga."


def _handle_water_stress_severe(signal: dict) -> str:
    """Severe water stress → urgent irrigation."""
    return "Tu campo está muy seco — riega hoy mismo antes de perder la cosecha."


def _handle_water_stress_moderate(signal: dict) -> str:
    """Moderate water stress → schedule irrigation soon."""
    return "El suelo está perdiendo humedad — riega pronto, no lo dejes para después."


def _handle_disease_risk_high(signal: dict) -> str:
    """High disease risk → immediate inspection."""
    return "Hay riesgo alto de plaga o enfermedad — revisa tus plantas hoy y aplica tratamiento."


def _handle_disease_risk_medium(signal: dict) -> str:
    """Medium disease risk → vigilance."""
    return "Vigila tus plantas estos días — puede estar llegando una enfermedad."


def _handle_frost(signal: dict) -> str:
    """Frost warning → protect crops tonight."""
    return "Viene helada esta noche — protege tus cultivos con cubierta o riego antes de que anochezca."


def _handle_heavy_rain(signal: dict) -> str:
    """Heavy rainfall → drainage warning."""
    return "Lluvia fuerte en camino — revisa que el campo no se encharte y cuida las raíces."


def _handle_unknown(signal: dict) -> str:
    return _FALLBACK


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

_HANDLERS: dict[str, object] = {
    "low_ndvi":              _handle_low_ndvi,
    "high_thermal":          _handle_high_thermal,
    "low_health":            _handle_low_health,
    "irrigation":            _handle_irrigation,
    "anomaly_health_drop":   _handle_anomaly_health_drop,
    "anomaly_ndvi_drop":     _handle_anomaly_ndvi_drop,
    "water_stress_severe":   _handle_water_stress_severe,
    "water_stress_moderate": _handle_water_stress_moderate,
    "disease_risk_high":     _handle_disease_risk_high,
    "disease_risk_medium":   _handle_disease_risk_medium,
    "frost":                 _handle_frost,
    "heavy_rain":            _handle_heavy_rain,
}
