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
    descripcion: str
    recomendacion: str
    urgencia: str  # alta, media, baja
    organico: bool


class DiseaseRiskResult(TypedDict):
    risk_level: str  # alto, medio, bajo, sin_riesgo
    mensaje: str
    risks: list[RiskItem]


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
            risks=[],
        )

    # Low NDVI + high thermal → disease risk
    if is_ndvi_stressed and is_thermal_stressed:
        risks.append(RiskItem(
            tipo="Enfermedad probable",
            descripcion=(
                f"NDVI bajo ({ndvi_mean:.2f}) combinado con estres termico alto "
                f"({thermal_stress_pct:.0f}% pixeles >35C). "
                "Patron consistente con infeccion fungica o bacteriana agravada por calor."
            ),
            recomendacion=(
                "Inspeccion visual inmediata del follaje. "
                "Aplicar te de composta foliar como preventivo (100 L/ha). "
                "Si se confirma hongo, aplicar caldo bordeles organico (sulfato de cobre + cal)."
            ),
            urgencia="alta",
            organico=True,
        ))

    # Patchy NDVI pattern → pest risk
    if is_patchy and is_ndvi_stressed:
        risks.append(RiskItem(
            tipo="Plaga probable",
            descripcion=(
                f"Alta variabilidad NDVI (std={ndvi_std:.2f}) indica dano irregular/parches. "
                "Patron consistente con ataque de plaga localizado."
            ),
            recomendacion=(
                "Inspeccionar zonas con NDVI bajo para identificar plaga especifica. "
                "Aplicar extracto de neem (5 ml/L) como repelente organico. "
                "Considerar trampas cromaticas amarillas para monitoreo."
            ),
            urgencia="alta" if stress_pct > 50 else "media",
            organico=True,
        ))

    # Low NDVI + low thermal + uniform → nutrient deficiency
    if is_ndvi_stressed and not is_thermal_stressed and not is_patchy:
        risks.append(RiskItem(
            tipo="Deficiencia de nutrientes probable",
            descripcion=(
                f"Declive uniforme de NDVI (media={ndvi_mean:.2f}, std={ndvi_std:.2f}) "
                "sin estres termico. Patron consistente con deficiencia nutricional o hidrica."
            ),
            recomendacion=(
                "Realizar analisis de suelo para confirmar deficiencias. "
                "Aplicar composta madura (5-10 ton/ha) como correccion general. "
                "Verificar sistema de riego y humedad del suelo."
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

    mensaje = f"{len(risks)} riesgo(s) detectado(s)" if risks else "Sin riesgo detectado"

    return DiseaseRiskResult(
        risk_level=risk_level,
        mensaje=mensaje,
        risks=risks,
    )
