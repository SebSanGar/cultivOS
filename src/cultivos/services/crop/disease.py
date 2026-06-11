"""Pure disease/pest identification service — matches symptoms to known diseases
and assesses risk from NDVI/thermal anomaly patterns."""

from typing import TypedDict


def identify_diseases(
    symptoms: list[str],
    diseases: list[dict],
    crop: str | None = None,
) -> list[dict]:
    """Match user-reported symptoms against known diseases.

    Args:
        symptoms: list of symptom strings (Spanish) reported by farmer
        diseases: list of disease dicts from DB (each has "symptoms", "affected_crops", etc.)
        crop: optional crop filter — only return diseases affecting this crop

    Returns:
        list of disease matches sorted by confidence (descending),
        each with added "confidence" and "symptoms_matched" fields
    """
    if not symptoms or not diseases:
        return []

    symptom_set = {s.lower().strip() for s in symptoms}
    matches = []

    for disease in diseases:
        # Filter by crop if specified
        if crop and crop.lower() not in [c.lower() for c in disease.get("affected_crops", [])]:
            continue

        disease_symptoms = {s.lower().strip() for s in disease.get("symptoms", [])}
        if not disease_symptoms:
            continue

        # Find overlapping symptoms
        matched = symptom_set & disease_symptoms
        if not matched:
            continue

        confidence = round(len(matched) / len(disease_symptoms), 2)

        matches.append({
            **disease,
            "confidence": confidence,
            "symptoms_matched": sorted(matched),
        })

    # Sort by confidence descending
    matches.sort(key=lambda m: m["confidence"], reverse=True)
    return matches


# -- NDVI anomaly-based risk assessment ---------------------------------------

# Thresholds for NDVI-based risk detection
NDVI_STRESS_THRESHOLD = 0.4  # mean below this = stressed
NDVI_PATCHY_STD_THRESHOLD = 0.15  # std above this = patchy (pest-like)
THERMAL_STRESS_THRESHOLD = 30.0  # % thermal pixels stressed
STRESS_PCT_THRESHOLD = 30.0  # % NDVI pixels below 0.4


class RiskItem(TypedDict):
    tipo: str
    tipo_en: str
    descripcion: str
    descripcion_en: str
    recomendacion: str
    recomendacion_en: str
    urgencia: str  # alta, media, baja
    organico: bool


class DiseaseRiskResult(TypedDict):
    risk_level: str  # alto, medio, bajo, sin_riesgo
    mensaje: str
    mensaje_en: str
    risks: list[RiskItem]


def _risk_mensaje(count: int) -> tuple[str, str]:
    """Build the bilingual risk-count summary message (es, en)."""
    if count:
        return (
            f"{count} riesgo(s) detectado(s)",
            f"{count} risk(s) detected",
        )
    return ("Sin riesgo detectado", "No risk detected")


def assess_disease_risk(
    ndvi_mean: float,
    stress_pct: float,
    thermal_stress_pct: float = 0.0,
    thermal_temp_mean: float = 25.0,
    ndvi_std: float = 0.10,
) -> DiseaseRiskResult:
    """Assess disease/pest risk from NDVI and thermal anomaly patterns.

    Decision logic:
    - Low NDVI + high thermal → likely disease (heat + pathogen)
    - Low NDVI + low thermal → likely nutrient deficiency
    - High NDVI std (patchy loss) → likely pest damage
    - Low NDVI std (uniform decline) → likely nutrient/water issue
    - Healthy NDVI → no risk detected
    """
    risks: list[RiskItem] = []

    is_ndvi_stressed = ndvi_mean < NDVI_STRESS_THRESHOLD or stress_pct > STRESS_PCT_THRESHOLD
    is_thermal_stressed = thermal_stress_pct > THERMAL_STRESS_THRESHOLD
    is_patchy = ndvi_std > NDVI_PATCHY_STD_THRESHOLD

    # Healthy field — no risk
    if not is_ndvi_stressed:
        return DiseaseRiskResult(
            risk_level="sin_riesgo",
            mensaje="Sin riesgo detectado",
            mensaje_en="No risk detected",
            risks=[],
        )

    # Low NDVI + high thermal → disease risk
    if is_ndvi_stressed and is_thermal_stressed:
        risks.append(RiskItem(
            tipo="Enfermedad probable",
            tipo_en="Probable disease",
            descripcion=(
                f"NDVI bajo ({ndvi_mean:.2f}) combinado con estres termico alto "
                f"({thermal_stress_pct:.0f}% pixeles >35C). "
                "Patron consistente con infeccion fungica o bacteriana agravada por calor."
            ),
            descripcion_en=(
                f"Low NDVI ({ndvi_mean:.2f}) combined with high thermal stress "
                f"({thermal_stress_pct:.0f}% of pixels >35C). "
                "Pattern consistent with a fungal or bacterial infection aggravated by heat."
            ),
            recomendacion=(
                "Inspeccion visual inmediata del follaje. "
                "Aplicar te de composta foliar como preventivo (100 L/ha). "
                "Si se confirma hongo, aplicar caldo bordeles organico (sulfato de cobre + cal)."
            ),
            recomendacion_en=(
                "Inspect the foliage visually right away. "
                "Apply foliar compost tea as a preventive (100 L/ha). "
                "If a fungus is confirmed, apply organic Bordeaux mixture (copper sulfate + lime)."
            ),
            urgencia="alta",
            organico=True,
        ))

    # Patchy NDVI pattern → pest risk
    if is_patchy and is_ndvi_stressed:
        risks.append(RiskItem(
            tipo="Plaga probable",
            tipo_en="Probable pest",
            descripcion=(
                f"Alta variabilidad NDVI (std={ndvi_std:.2f}) indica dano irregular/parches. "
                "Patron consistente con ataque de plaga localizado."
            ),
            descripcion_en=(
                f"High NDVI variability (std={ndvi_std:.2f}) points to irregular, patchy damage. "
                "Pattern consistent with a localized pest attack."
            ),
            recomendacion=(
                "Inspeccionar zonas con NDVI bajo para identificar plaga especifica. "
                "Aplicar extracto de neem (5 ml/L) como repelente organico. "
                "Considerar trampas cromaticas amarillas para monitoreo."
            ),
            recomendacion_en=(
                "Scout the low-NDVI zones to identify the specific pest. "
                "Apply neem extract (5 ml/L) as an organic repellent. "
                "Consider yellow sticky traps for monitoring."
            ),
            urgencia="alta" if stress_pct > 50 else "media",
            organico=True,
        ))

    # Low NDVI + low thermal + uniform → nutrient deficiency
    if is_ndvi_stressed and not is_thermal_stressed and not is_patchy:
        risks.append(RiskItem(
            tipo="Deficiencia de nutrientes probable",
            tipo_en="Probable nutrient deficiency",
            descripcion=(
                f"Declive uniforme de NDVI (media={ndvi_mean:.2f}, std={ndvi_std:.2f}) "
                "sin estres termico. Patron consistente con deficiencia nutricional o hidrica."
            ),
            descripcion_en=(
                f"Uniform NDVI decline (mean={ndvi_mean:.2f}, std={ndvi_std:.2f}) "
                "with no thermal stress. Pattern consistent with a nutrient or water deficiency."
            ),
            recomendacion=(
                "Realizar analisis de suelo para confirmar deficiencias. "
                "Aplicar composta madura (5-10 ton/ha) como correccion general. "
                "Verificar sistema de riego y humedad del suelo."
            ),
            recomendacion_en=(
                "Run a soil test to confirm the deficiencies. "
                "Apply mature compost (5-10 t/ha) as a general correction. "
                "Check the irrigation system and soil moisture."
            ),
            urgencia="media",
            organico=True,
        ))

    # Determine overall risk level
    if any(r["urgencia"] == "alta" for r in risks):
        risk_level = "alto"
    elif risks:
        risk_level = "medio"
    else:
        risk_level = "sin_riesgo"

    mensaje, mensaje_en = _risk_mensaje(len(risks))

    return DiseaseRiskResult(
        risk_level=risk_level,
        mensaje=mensaje,
        mensaje_en=mensaje_en,
        risks=risks,
    )


# -- Weather-enhanced risk assessment -----------------------------------------

HUMIDITY_FUNGAL_THRESHOLD = 80.0  # % — above this, fungal conditions favorable
RAINFALL_FUNGAL_THRESHOLD = 5.0  # mm — recent rain creates moisture for fungi
TEMP_FUNGAL_MIN = 20.0  # C — fungi need warmth
TEMP_FUNGAL_MAX = 35.0  # C — most pathogens thrive in this range


class WeatherContext(TypedDict):
    humidity_pct: float
    rainfall_mm: float
    temp_c: float


class DiseaseWeatherResult(TypedDict):
    risk_level: str  # alto, medio, bajo, sin_riesgo
    mensaje: str
    mensaje_en: str
    risks: list[RiskItem]
    weather_context: WeatherContext


def assess_disease_weather_risk(
    ndvi_mean: float,
    stress_pct: float,
    thermal_stress_pct: float = 0.0,
    thermal_temp_mean: float = 25.0,
    ndvi_std: float = 0.10,
    humidity_pct: float = 50.0,
    rainfall_mm: float = 0.0,
    temp_c: float = 25.0,
) -> DiseaseWeatherResult:
    """Assess disease risk combining NDVI/thermal anomalies with weather conditions.

    Extends assess_disease_risk by adding fungal risk detection:
    - High humidity (>80%) + recent rainfall (>5mm) + warm temps (20-35C) = fungal risk
    - This can elevate risk even when NDVI alone looks borderline

    Args:
        ndvi_mean: mean NDVI value (0-1)
        stress_pct: % of NDVI pixels below stress threshold
        thermal_stress_pct: % of thermal pixels above 35C
        thermal_temp_mean: mean temperature from thermal sensor (C)
        ndvi_std: standard deviation of NDVI values
        humidity_pct: current relative humidity (%)
        rainfall_mm: recent rainfall in mm
        temp_c: current air temperature (C)

    Returns:
        DiseaseWeatherResult with risk assessment including weather context
    """
    # Start with base NDVI/thermal risk assessment
    base = assess_disease_risk(
        ndvi_mean=ndvi_mean,
        stress_pct=stress_pct,
        thermal_stress_pct=thermal_stress_pct,
        thermal_temp_mean=thermal_temp_mean,
        ndvi_std=ndvi_std,
    )

    risks: list[RiskItem] = list(base["risks"])

    # Check fungal-favorable weather conditions
    is_humid = humidity_pct >= HUMIDITY_FUNGAL_THRESHOLD
    has_rain = rainfall_mm >= RAINFALL_FUNGAL_THRESHOLD
    is_warm = TEMP_FUNGAL_MIN <= temp_c <= TEMP_FUNGAL_MAX

    if is_humid and has_rain and is_warm:
        severity = "alta"
        if humidity_pct >= 90.0 and rainfall_mm >= 20.0:
            severity = "alta"
        elif humidity_pct < 85.0 or rainfall_mm < 10.0:
            severity = "media"

        risks.append(RiskItem(
            tipo="Riesgo fungico por clima",
            tipo_en="Weather-driven fungal risk",
            descripcion=(
                f"Condiciones climaticas favorables para hongos: "
                f"humedad alta ({humidity_pct:.0f}%), "
                f"lluvia reciente ({rainfall_mm:.0f}mm), "
                f"temperatura {temp_c:.0f}C. "
                "Ambiente propicio para desarrollo de enfermedades fungicas "
                "como roya, tizon, y mildiu."
            ),
            descripcion_en=(
                f"Weather conditions favor fungal growth: "
                f"high humidity ({humidity_pct:.0f}%), "
                f"recent rainfall ({rainfall_mm:.0f}mm), "
                f"temperature {temp_c:.0f}C. "
                "An environment conducive to fungal diseases "
                "such as rust, blight, and mildew."
            ),
            recomendacion=(
                "Monitoreo preventivo del follaje cada 2-3 dias. "
                "Aplicar caldo bordeles organico (sulfato de cobre + cal) como preventivo. "
                "Mejorar ventilacion entre plantas si es posible. "
                "Evitar riego por aspersion durante periodo humedo."
            ),
            recomendacion_en=(
                "Scout the foliage preventively every 2-3 days. "
                "Apply organic Bordeaux mixture (copper sulfate + lime) as a preventive. "
                "Improve airflow between plants where possible. "
                "Avoid overhead irrigation during the humid period."
            ),
            urgencia=severity,
            organico=True,
        ))

    # Determine overall risk level
    if any(r["urgencia"] == "alta" for r in risks):
        risk_level = "alto"
    elif risks:
        risk_level = "medio"
    else:
        risk_level = "sin_riesgo"

    mensaje, mensaje_en = _risk_mensaje(len(risks))

    return DiseaseWeatherResult(
        risk_level=risk_level,
        mensaje=mensaje,
        mensaje_en=mensaje_en,
        risks=risks,
        weather_context=WeatherContext(
            humidity_pct=humidity_pct,
            rainfall_mm=rainfall_mm,
            temp_c=temp_c,
        ),
    )
