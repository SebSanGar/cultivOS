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


class Treatment(TypedDict, total=False):
    problema: str
    causa_probable: str
    tratamiento: str
    costo_estimado_mxn: int
    urgencia: str  # alta, media, baja
    prevencion: str
    organic: bool
    metodo_ancestral: str | None
    base_cientifica: str | None
    razon_match: str | None


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


def recommend_treatment(
    health_score: float,
    soil: SoilInput | None = None,
    crop_type: str | None = None,
    microbiome: MicrobiomeInput | None = None,
    ancestral_methods: list[AncestralMethodData] | None = None,
) -> list[Treatment]:
    """Generate organic treatment recommendations based on health score, soil, and microbiome.

    Returns a list of Treatment dicts. Healthy fields (score > 80) get a single
    "no treatment needed" entry. Lower scores trigger specific recommendations
    based on soil deficiencies and microbiome degradation.

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

    return recommendations
