"""Pure treatment recommendation engine — data in, recommendations out.

No HTTP, no DB, no side effects. Regenerative-first: never recommends
synthetic pesticides or fertilizers. Links recommendations to ancestral
methods when available (TEK integration for FODECIJAL).
"""

from typing import TypedDict


class SoilInput(TypedDict, total=False):
    ph: float | None
    organic_matter_pct: float | None
    nitrogen_ppm: float | None
    phosphorus_ppm: float | None
    potassium_ppm: float | None
    moisture_pct: float | None


class MicrobiomeInput(TypedDict, total=False):
    respiration_rate: float
    microbial_biomass_carbon: float
    fungi_bacteria_ratio: float
    classification: str  # healthy, moderate, degraded


class AncestralMethodData(TypedDict, total=False):
    name: str
    practice_type: str  # intercropping, soil_management, water_management
    crops: list[str]
    benefits_es: str
    scientific_basis: str


class ForecastInput(TypedDict, total=False):
    temp_c: float
    humidity_pct: float
    wind_kmh: float
    description: str


class WeatherInput(TypedDict, total=False):
    temp_c: float
    humidity_pct: float
    wind_kmh: float
    description: str
    forecast_3day: list[ForecastInput]


class RegionInput(TypedDict, total=False):
    region_name: str
    climate_zone: str
    soil_type: str
    growing_season: str
    key_crops: list[str]
    currency: str
    seasonal_notes: str


class Treatment(TypedDict, total=False):
    problema: str
    causa_probable: str
    tratamiento: str
    costo_estimado_mxn: int
    costo_estimado_cad: float | None
    urgencia: str  # alta, media, baja
    prevencion: str
    organic: bool
    metodo_ancestral: str | None
    base_cientifica: str | None
    razon_match: str | None
    timing_consejo: str | None
    contexto_regional: str | None


_NO_TREATMENT = Treatment(
    problema="Sin tratamiento necesario",
    causa_probable="Campo en buen estado",
    tratamiento="Continuar manejo actual",
    costo_estimado_mxn=0,
    urgencia="baja",
    prevencion="Monitoreo regular cada 2 semanas",
    organic=True,
    metodo_ancestral=None,
    base_cientifica=None,
    razon_match=None,
)

# Maps treatment problem keywords to ancestral practice_types that address them
_PROBLEM_TO_PRACTICE_TYPE: dict[str, list[str]] = {
    "organica": ["soil_management"],       # low organic matter
    "nitrogeno": ["intercropping", "soil_management"],  # nitrogen deficiency
    "fosforo": ["soil_management"],        # phosphorus deficiency
    "potasio": ["soil_management"],        # potassium deficiency
    "humedad": ["water_management", "soil_management"],  # low moisture
    "microbioma": ["soil_management"],     # degraded microbiome
    "hongos:bacterias": ["soil_management"],  # low fungi:bacteria ratio
    "ph": ["soil_management"],             # pH issues
    "estres general": ["intercropping", "soil_management"],  # general stress
}


def _match_ancestral(
    problema: str,
    crop_type: str | None,
    ancestral_methods: list[AncestralMethodData],
) -> tuple[str | None, str | None, str | None]:
    """Match a treatment problem to the best ancestral method.

    Returns (method_name, scientific_basis, reason) or (None, None, None).
    """
    if not ancestral_methods:
        return None, None, None

    problema_lower = problema.lower()

    # Find which practice types are relevant for this problem
    matching_types: list[str] = []
    for keyword, types in _PROBLEM_TO_PRACTICE_TYPE.items():
        if keyword in problema_lower:
            matching_types.extend(types)

    if not matching_types:
        return None, None, None

    # Filter ancestral methods by: practice_type matches AND crop is compatible
    # Group by practice_type priority (first matching type in list wins)
    candidates_by_type: dict[str, list[AncestralMethodData]] = {}
    for method in ancestral_methods:
        ptype = method.get("practice_type")
        if ptype not in matching_types:
            continue
        # If crop_type specified, method must support that crop
        if crop_type and method.get("crops"):
            if crop_type.lower() not in [c.lower() for c in method["crops"]]:
                continue
        candidates_by_type.setdefault(ptype, []).append(method)

    if not candidates_by_type:
        return None, None, None

    # Pick the best candidate: prefer the first practice_type in matching_types order
    best = None
    for ptype in matching_types:
        if ptype in candidates_by_type:
            best = candidates_by_type[ptype][0]
            break
    if best is None:
        return None, None, None
    reason = f"Practica {best.get('practice_type', '')} validada para {crop_type or 'cultivos generales'}"
    return best["name"], best.get("scientific_basis"), reason


def _has_rain_forecast(weather: WeatherInput | None) -> bool:
    """Check if any forecast day mentions rain."""
    if not weather:
        return False
    for day in weather.get("forecast_3day", []):
        desc = day.get("description", "").lower()
        if "lluvia" in desc or "rain" in desc or "tormenta" in desc:
            return True
    return False


def _rain_in_24h(weather: WeatherInput | None) -> bool:
    """Check if rain is expected in the first forecast day (next 24h)."""
    if not weather:
        return False
    forecast = weather.get("forecast_3day", [])
    if not forecast:
        return False
    desc = forecast[0].get("description", "").lower()
    return "lluvia" in desc or "rain" in desc or "tormenta" in desc


def _is_extreme_heat(weather: WeatherInput | None) -> bool:
    """Check if current or forecast temps exceed 38C."""
    if not weather:
        return False
    if weather.get("temp_c", 0) >= 38:
        return True
    for day in weather.get("forecast_3day", []):
        if day.get("temp_c", 0) >= 38:
            return True
    return False


def _is_drought_conditions(weather: WeatherInput | None) -> bool:
    """Check for dry/hot conditions: high temp, low humidity, no rain."""
    if not weather:
        return False
    if weather.get("humidity_pct", 50) > 40:
        return False
    if _has_rain_forecast(weather):
        return False
    if weather.get("temp_c", 0) >= 32:
        return True
    return False


def _compute_timing(rec: Treatment, weather: WeatherInput | None) -> str:
    """Compute timing advice for a recommendation based on weather forecast."""
    if not weather:
        return ""

    problema = rec.get("problema", "").lower()
    tratamiento = rec.get("tratamiento", "").lower()

    # Foliar sprays and liquid applications should wait if rain in 24h
    # "te de composta" is a liquid application (not a solid amendment)
    is_foliar = "foliar" in tratamiento or "te de composta" in tratamiento or "te de" in tratamiento
    if is_foliar and _rain_in_24h(weather):
        return "Esperar a que pase la lluvia (pronostico de lluvia en 24h) — aplicar despues para evitar lavado"

    # Solid organic amendments (composta madura, abono, compost) benefit from rain
    is_amendment = ("composta" in tratamiento or "abono" in tratamiento or "compost" in tratamiento) and not is_foliar
    if is_amendment and _has_rain_forecast(weather):
        if _rain_in_24h(weather):
            return "Aplicar ahora antes de la lluvia pronosticada en 24h — la lluvia ayuda a incorporar la materia organica"
        return "Aplicar antes de la lluvia pronosticada — la humedad ayuda a incorporar la materia organica"

    # Extreme heat — apply early morning
    if _is_extreme_heat(weather):
        return "Aplicar temprano (6-8 AM) — calor extremo pronosticado, evitar horas de mayor temperatura"

    # Drought conditions — prioritize water-related treatments
    if _is_drought_conditions(weather):
        return "Condiciones de sequia pronosticadas — priorizar riego y acolchado antes de aplicar tratamientos al suelo"

    return ""


def recommend_treatment(
    health_score: float,
    soil: SoilInput | None = None,
    crop_type: str | None = None,
    microbiome: MicrobiomeInput | None = None,
    ancestral_methods: list[AncestralMethodData] | None = None,
    weather: WeatherInput | None = None,
    growth_stage: str | None = None,
    region: RegionInput | None = None,
) -> list[Treatment]:
    """Generate organic treatment recommendations based on health score, soil, microbiome, and weather.

    Returns a list of Treatment dicts. Healthy fields (score > 80) get a single
    "no treatment needed" entry. Lower scores trigger specific recommendations
    based on soil deficiencies, microbiome degradation, and weather conditions.

    When weather data is provided, recommendations include timing advice and
    weather-triggered treatments (drought resilience, heat protection).

    When ancestral_methods are provided, each recommendation is enriched with
    the best matching traditional practice and its scientific validation.
    """
    if health_score > 80:
        return [_NO_TREATMENT]

    ancestral = ancestral_methods or []

    recommendations: list[Treatment] = []
    soil = soil or {}
    microbiome = microbiome or {}

    # High pH — alkaline soil needs acidification
    ph = soil.get("ph")
    if ph is not None and ph > 7.5:
        recommendations.append(Treatment(
            problema="pH alcalino — acidificar suelo",
            causa_probable="Acumulacion de sales o riego con agua alcalina",
            tratamiento="Aplicar azufre elemental (2-3 kg/ha) o compost acido de hojarasca de pino",
            costo_estimado_mxn=800,
            urgencia="alta" if ph > 8.5 else "media",
            prevencion="Usar mulch organico acido, compostas con hojarasca de coniferas",
            organic=True,
        ))

    # Low pH — acidic soil needs liming
    if ph is not None and ph < 5.5:
        recommendations.append(Treatment(
            problema="pH acido — encalar suelo",
            causa_probable="Suelo naturalmente acido o sobreuso de materia organica acida",
            tratamiento="Aplicar cal dolomitica (1-2 ton/ha) o ceniza de madera (500 kg/ha)",
            costo_estimado_mxn=1500,
            urgencia="alta" if ph < 4.5 else "media",
            prevencion="Monitorear pH cada 6 meses, alternar cultivos fijadores de nitrogeno",
            organic=True,
        ))

    # Low organic matter
    om = soil.get("organic_matter_pct")
    if om is not None and om < 2.0:
        recommendations.append(Treatment(
            problema="Materia organica baja",
            causa_probable="Suelo degradado, falta de cobertura vegetal o quema de rastrojo",
            tratamiento="Incorporar composta madura (5-10 ton/ha), sembrar cultivos de cobertura (veza, trebol)",
            costo_estimado_mxn=3000,
            urgencia="alta" if om < 1.0 else "media",
            prevencion="No quemar rastrojo, rotar con leguminosas, aplicar acolchado organico",
            organic=True,
        ))

    # Low nitrogen
    n = soil.get("nitrogen_ppm")
    if n is not None and n < 15:
        recommendations.append(Treatment(
            problema="Deficiencia de nitrogeno",
            causa_probable="Suelo agotado, falta de rotacion con leguminosas",
            tratamiento="Aplicar te de composta (200 L/ha), sembrar frijol o veza como cultivo de cobertura",
            costo_estimado_mxn=1200,
            urgencia="alta" if n < 8 else "media",
            prevencion="Rotar con leguminosas cada ciclo, incorporar abono verde",
            organic=True,
        ))

    # Low phosphorus
    p = soil.get("phosphorus_ppm")
    if p is not None and p < 10:
        recommendations.append(Treatment(
            problema="Deficiencia de fosforo",
            causa_probable="Suelo fijador de fosforo o extraccion sin reposicion",
            tratamiento="Aplicar harina de hueso (1 kg/m2) o roca fosforica (500 kg/ha)",
            costo_estimado_mxn=2000,
            urgencia="media",
            prevencion="Inocular micorrizas, mantener pH entre 6.0-7.0 para disponibilidad de P",
            organic=True,
        ))

    # Low potassium
    k = soil.get("potassium_ppm")
    if k is not None and k < 80:
        recommendations.append(Treatment(
            problema="Deficiencia de potasio",
            causa_probable="Suelo arenoso lixiviado o extraccion intensiva",
            tratamiento="Aplicar ceniza de madera (300 kg/ha) o te de platano/comfrey",
            costo_estimado_mxn=600,
            urgencia="media",
            prevencion="Reciclar cenizas, usar mulch de platano, compostar restos de cosecha",
            organic=True,
        ))

    # Low moisture
    moisture = soil.get("moisture_pct")
    if moisture is not None and moisture < 15:
        recommendations.append(Treatment(
            problema="Humedad del suelo baja",
            causa_probable="Deficit de riego, alta evaporacion o suelo sin cobertura",
            tratamiento="Aplicar acolchado organico (10 cm paja/hojarasca), instalar riego por goteo",
            costo_estimado_mxn=2500,
            urgencia="alta" if moisture < 8 else "media",
            prevencion="Mantener cobertura permanente, riego temprano (6-8 AM), zanjas de infiltracion",
            organic=True,
        ))

    # Degraded microbiome — needs biological restoration
    micro_class = microbiome.get("classification")
    if micro_class == "degraded":
        recommendations.append(Treatment(
            problema="Microbioma del suelo degradado",
            causa_probable="Baja actividad microbiana por uso excesivo de agroquimicos, compactacion o falta de materia organica",
            tratamiento="Aplicar te de composta aireado (200 L/ha), inocular micorrizas (2 kg/ha), sembrar cultivos de cobertura multiespecies",
            costo_estimado_mxn=2500,
            urgencia="alta",
            prevencion="Mantener cobertura vegetal permanente, no usar agroquimicos sinteticos, incorporar composta cada ciclo",
            organic=True,
        ))

    # Low fungi:bacteria ratio — soil ecosystem immature
    fbr = microbiome.get("fungi_bacteria_ratio")
    if fbr is not None and fbr < 0.5 and micro_class != "healthy":
        recommendations.append(Treatment(
            problema="Relacion hongos:bacterias baja — ecosistema del suelo inmaduro",
            causa_probable="Labranza excesiva destruye redes de micelio, suelo perturbado",
            tratamiento="Reducir labranza, aplicar mulch de madera (5-10 cm), inocular hongos micorrizicos",
            costo_estimado_mxn=1800,
            urgencia="media",
            prevencion="Labranza minima o cero, mantener raices vivas en el suelo todo el ano",
            organic=True,
        ))

    # Weather-triggered recommendations
    if weather and _is_extreme_heat(weather):
        max_temp = max(
            weather.get("temp_c", 0),
            *(d.get("temp_c", 0) for d in weather.get("forecast_3day", [])),
        )
        recommendations.append(Treatment(
            problema=f"Calor extremo pronosticado ({max_temp:.0f}C)",
            causa_probable="Ola de calor — riesgo de estres termico y deshidratacion del cultivo",
            tratamiento="Aplicar acolchado organico grueso (15 cm paja), riego por goteo temprano (5-7 AM), malla sombra si disponible",
            costo_estimado_mxn=3500,
            urgencia="alta",
            prevencion="Mantener cobertura vegetal permanente, seleccionar variedades resistentes al calor",
            organic=True,
        ))

    if weather and _is_drought_conditions(weather):
        recommendations.append(Treatment(
            problema="Condiciones de sequia pronosticadas",
            causa_probable=f"Humedad baja ({weather.get('humidity_pct', 0):.0f}%), sin lluvia pronosticada, temperatura alta",
            tratamiento="Aplicar mulch organico (10-15 cm), reducir frecuencia de riego pero aumentar profundidad, priorizar cultivos de cobertura",
            costo_estimado_mxn=2000,
            urgencia="alta",
            prevencion="Zanjas de infiltracion, cosecha de agua de lluvia, seleccion de cultivos resistentes a sequia",
            organic=True,
        ))

    # General stress with no specific soil cause identified
    if not recommendations and health_score <= 80:
        recommendations.append(Treatment(
            problema="Estres general del cultivo",
            causa_probable="Multiples factores — revisar datos de vuelo y observacion en campo",
            tratamiento="Aplicar te de composta foliar (100 L/ha), revisar riego y plagas manualmente",
            costo_estimado_mxn=800,
            urgencia="alta" if health_score < 30 else "media",
            prevencion="Monitoreo semanal con dron, observacion directa en campo cada 3 dias",
            organic=True,
        ))

    # Enrich each recommendation with matching ancestral method
    for rec in recommendations:
        name, basis, reason = _match_ancestral(rec["problema"], crop_type, ancestral)
        rec["metodo_ancestral"] = name
        rec["base_cientifica"] = basis
        rec["razon_match"] = reason

    # Add weather-based timing advice to each recommendation
    for rec in recommendations:
        rec["timing_consejo"] = _compute_timing(rec, weather)

    # Add growth stage context to treatment descriptions
    if growth_stage:
        _STAGE_GUIDANCE: dict[str, str] = {
            "siembra": "En etapa de siembra: priorizar desarrollo radicular, aplicaciones suaves",
            "vegetativo": "En etapa vegetativa: priorizar nitrogeno para crecimiento foliar",
            "floracion": "En etapa de floracion: evitar estres hidrico, priorizar potasio y fosforo",
            "fructificacion": "En etapa de fructificacion: priorizar potasio para frutos, calcio para firmeza",
            "cosecha": "En etapa de cosecha: reducir insumos, preparar suelo para siguiente ciclo",
        }
        guidance = _STAGE_GUIDANCE.get(growth_stage, "")
        if guidance:
            for rec in recommendations:
                existing = rec.get("prevencion", "")
                rec["prevencion"] = f"{guidance}. {existing}"

    # Add region-specific context to each recommendation
    _enrich_with_region(recommendations, region)

    return recommendations


# ── Region enrichment ─────────────────────────────────────────────────


# MXN to CAD approximate conversion factor
_MXN_TO_CAD = 0.075


def _enrich_with_region(
    recommendations: list[Treatment],
    region: RegionInput | None,
) -> None:
    """Inject region metadata into each recommendation (mutates in place)."""
    if not region:
        for rec in recommendations:
            rec["contexto_regional"] = None
            rec["costo_estimado_cad"] = None
        return

    climate = region.get("climate_zone", "")
    soil_type = region.get("soil_type", "")
    seasonal = region.get("seasonal_notes", "")
    currency = region.get("currency", "MXN")

    for rec in recommendations:
        # Build regional context note
        parts: list[str] = []
        if climate and climate != "generic":
            parts.append(f"Zona climatica: {climate}")
        if soil_type:
            parts.append(f"Suelo: {soil_type}")
        if seasonal:
            parts.append(f"Nota estacional: {seasonal}")

        rec["contexto_regional"] = " | ".join(parts) if parts else None

        # Add CAD cost estimate for Canadian regions
        if currency == "CAD":
            mxn_cost = rec.get("costo_estimado_mxn", 0)
            rec["costo_estimado_cad"] = round(mxn_cost * _MXN_TO_CAD, 2) if mxn_cost else None
        else:
            rec["costo_estimado_cad"] = None


# ── Treatment timing optimizer ─────────────────────────────────────────


class TimingResult(TypedDict):
    best_day: int
    best_time: str
    reason: str
    avoid_days: list[int]


_RAIN_KEYWORDS = ("lluvia", "rain", "tormenta")
_HEAVY_RAIN_KEYWORDS = ("tormenta fuerte", "heavy rain", "lluvia fuerte")


def _day_has_rain(day: ForecastInput) -> bool:
    desc = day.get("description", "").lower()
    return any(kw in desc for kw in _RAIN_KEYWORDS)


def _day_has_heavy_rain(day: ForecastInput) -> bool:
    desc = day.get("description", "").lower()
    return any(kw in desc for kw in _HEAVY_RAIN_KEYWORDS)


def _rain_severity(day: ForecastInput) -> int:
    """0 = no rain, 1 = light, 2 = moderate, 3 = heavy/storm."""
    desc = day.get("description", "").lower()
    if any(kw in desc for kw in _HEAVY_RAIN_KEYWORDS):
        return 3
    if "moderada" in desc or "moderate" in desc:
        return 2
    if any(kw in desc for kw in _RAIN_KEYWORDS):
        return 1
    return 0


def _has_extreme_heat(forecast: list[ForecastInput]) -> bool:
    return any(d.get("temp_c", 0) >= 38 for d in forecast)


def optimize_treatment_timing(
    treatment_type: str,
    forecast_3day: list[ForecastInput],
) -> TimingResult:
    """Recommend the optimal day and time to apply a treatment based on 3-day forecast.

    Pure function — no DB, no HTTP.

    Args:
        treatment_type: one of "organic_amendment", "foliar_spray", "soil_drench"
        forecast_3day: list of up to 3 ForecastInput dicts

    Returns:
        TimingResult with best_day (0-2), best_time, reason, avoid_days.
    """
    if not forecast_3day:
        return TimingResult(
            best_day=0,
            best_time="Temprano en la mañana (6-8 AM)",
            reason="Sin datos de pronostico — aplicar lo antes posible",
            avoid_days=[],
        )

    # Determine early-morning recommendation if any day has extreme heat
    heat_warning = _has_extreme_heat(forecast_3day)
    default_time = "Temprano en la mañana (6-8 AM)" if heat_warning else "Temprano en la mañana (6-8 AM)"

    avoid_days: list[int] = []

    if treatment_type == "organic_amendment":
        return _optimize_amendment(forecast_3day, default_time)
    elif treatment_type == "foliar_spray":
        return _optimize_foliar(forecast_3day, default_time)
    elif treatment_type == "soil_drench":
        return _optimize_soil_drench(forecast_3day, default_time)
    else:
        # Unknown type — default to first calm day
        return TimingResult(
            best_day=0,
            best_time=default_time,
            reason="Tipo de tratamiento no reconocido — aplicar en condiciones favorables",
            avoid_days=[],
        )


def _optimize_amendment(
    forecast: list[ForecastInput], default_time: str
) -> TimingResult:
    """Organic amendments benefit from rain (helps incorporation).
    Best day: the day BEFORE rain. If rain is day 0, apply day 0.
    No rain: pick the coolest day.
    """
    rain_days = [i for i, d in enumerate(forecast) if _day_has_rain(d)]

    if rain_days:
        first_rain = rain_days[0]
        best_day = max(0, first_rain - 1) if first_rain > 0 else 0
        if first_rain == 0:
            reason = "Lluvia hoy — aplicar ahora, la lluvia ayuda a incorporar la materia organica"
        else:
            reason = f"Aplicar antes de la lluvia pronosticada (dia {first_rain + 1}) — la humedad ayuda a incorporar la materia organica"
        return TimingResult(
            best_day=best_day,
            best_time=default_time,
            reason=reason,
            avoid_days=[],
        )

    # No rain — pick coolest day
    temps = [d.get("temp_c", 30.0) for d in forecast]
    coolest = temps.index(min(temps))
    return TimingResult(
        best_day=coolest,
        best_time=default_time,
        reason=f"Sin lluvia pronosticada — aplicar el dia mas fresco ({temps[coolest]:.0f}C)",
        avoid_days=[],
    )


def _optimize_foliar(
    forecast: list[ForecastInput], default_time: str
) -> TimingResult:
    """Foliar sprays are washed off by rain and drift in wind.
    Avoid: rain days, wind > 20 km/h.
    If all days have rain, pick lightest rain.
    """
    avoid_days: list[int] = []

    for i, d in enumerate(forecast):
        if _day_has_rain(d):
            avoid_days.append(i)
        elif d.get("wind_kmh", 0) > 20:
            avoid_days.append(i)

    good_days = [i for i in range(len(forecast)) if i not in avoid_days]

    if good_days:
        best_day = good_days[0]
        reason = "Dia sin lluvia ni viento fuerte — condiciones optimas para aplicacion foliar"
        return TimingResult(
            best_day=best_day,
            best_time=default_time,
            reason=reason,
            avoid_days=avoid_days,
        )

    # All days have issues — pick the one with lightest rain
    severities = [_rain_severity(d) for d in forecast]
    # Among rain days, also factor in wind
    scores = []
    for i, d in enumerate(forecast):
        score = severities[i] * 10 + max(0, d.get("wind_kmh", 0) - 10)
        scores.append(score)
    best_day = scores.index(min(scores))
    return TimingResult(
        best_day=best_day,
        best_time=default_time,
        reason="Todos los dias tienen lluvia — seleccionado el dia con lluvia mas ligera",
        avoid_days=[i for i in range(len(forecast)) if i != best_day],
    )


def _optimize_soil_drench(
    forecast: list[ForecastInput], default_time: str
) -> TimingResult:
    """Soil drenches need soil to absorb the liquid — avoid saturated soil
    (day after heavy rain) and rain days (dilution).
    """
    avoid_days: list[int] = []

    for i, d in enumerate(forecast):
        if _day_has_heavy_rain(d):
            avoid_days.append(i)
            # Day after heavy rain is also bad (saturated)
            if i + 1 < len(forecast):
                avoid_days.append(i + 1)
        elif _day_has_rain(d):
            avoid_days.append(i)

    avoid_days = sorted(set(avoid_days))
    good_days = [i for i in range(len(forecast)) if i not in avoid_days]

    if good_days:
        # Prefer driest day (lowest humidity)
        best_day = min(good_days, key=lambda i: forecast[i].get("humidity_pct", 50))
        reason = "Suelo no saturado — condiciones optimas para absorcion del drench"
    else:
        # All days problematic — pick last day (most time for soil to dry)
        best_day = len(forecast) - 1
        reason = "Suelo puede estar saturado — esperar al ultimo dia para mayor secado"

    return TimingResult(
        best_day=best_day,
        best_time=default_time,
        reason=reason,
        avoid_days=avoid_days,
    )
