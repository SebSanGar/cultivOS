"""Farmer query simulator — pattern-based Spanish agriculture issue detection.

Pure function: no I/O, no DB, no HTTP. Takes a Spanish text message and optional
crop context, returns a structured response suitable for a WhatsApp demo.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Issue patterns: (regex, issue_label, severity, action_es)
# Ordered by specificity — first match wins.
# ---------------------------------------------------------------------------
_ISSUE_PATTERNS: list[tuple[str, str, str, str]] = [
    (
        r"mancha[s]?\s*(amarilla[s]?|cafe[s]?|negra[s]?|caf[eé][s]?)|"
        r"hoja[s]?\s*(amarilla[s]?|seca[s]?|manchada[s]?)|"
        r"amarillez|clorosis",
        "mancha foliar / posible enfermedad fúngica",
        "medium",
        "Aplique caldo bordelés (cobre + cal) en las hojas afectadas. "
        "Evite el riego por aspersión por las tardes. "
        "Retire y queme las hojas con manchas para detener el avance.",
    ),
    (
        r"hongo[s]?|mildiu|tizón|tiz[oó]n|pudrici[oó]n|moho",
        "enfermedad fúngica",
        "high",
        "Aplique extracto de nim o caldo de cobre. "
        "Mejore la ventilación entre plantas espaciando más los surcos. "
        "Evite exceso de humedad en el suelo.",
    ),
    (
        r"insecto[s]?|plaga[s]?|gusano[s]?|pulgón|pul[gó]n|"
        r"mosca[s]?|chapulín|chapul[ií]n|escarabajo[s]?|larva[s]?",
        "ataque de plagas / insectos",
        "high",
        "Aplique extracto de ajo-chile o jabón potásico sobre el follaje. "
        "Instale trampas amarillas pegajosas. "
        "Favorezca la presencia de depredadores naturales como mariquitas.",
    ),
    (
        r"seca|sequía|sequ[ií]a|no ha llovido|falta de agua|"
        r"tierra seca|suelo seco|marchit",
        "estrés hídrico / sequía",
        "high",
        "Aplique riego de rescate por goteo enfocado en la zona radical. "
        "Cubra el suelo con mulch (rastrojo o paja) para retener humedad. "
        "Reduzca la evapotranspiración podando hojas dañadas.",
    ),
    (
        r"mucho\s*agua|encharcado|encharcamiento|inundac|exceso\s*de\s*(agua|riego)|"
        r"agua\s*estancada|pa[uú]l",
        "encharcamiento / exceso de agua",
        "medium",
        "Abra zanjas de drenaje entre surcos. "
        "Evite regar hasta que el suelo drene. "
        "Aplique vermicomposta para mejorar la estructura del suelo.",
    ),
    (
        r"nutriente[s]?|deficiencia|nitrógeno|n[ií]trogeno|f[oó]sforo|fosforo|"
        r"pot[aá]sio|potasio|crecimiento\s*lento|planta[s]?\s*(pequeña[s]?|débil|debil)",
        "deficiencia nutricional",
        "medium",
        "Aplique té de composta o biol (fertilizante líquido fermentado). "
        "Incorpore leguminosas como fijadoras de nitrógeno. "
        "Realice análisis de suelo para identificar el nutriente limitante.",
    ),
    (
        r"enfermedad|virus|bacterial|bacteria|costra|"
        r"tallo\s*(podrido|negro|blando)|cuello\s*podrido",
        "posible enfermedad bacteriana o viral",
        "high",
        "Retire y destruya las plantas afectadas para evitar contagio. "
        "Aplique caldo bordelés como preventivo en plantas vecinas. "
        "Consulte con un agrónomo local para diagnóstico preciso.",
    ),
    (
        r"helada|frío|fr[ií]o|temperatura\s*baja|escarcha",
        "daño por helada",
        "high",
        "Cubra las plantas con tela agroterm o plástico durante la noche. "
        "Aplique riego ligero antes de la madrugada para elevar temperatura. "
        "Pode las partes dañadas una vez pasado el riesgo de helada.",
    ),
    (
        r"viento|tallo\s*(ca[ií]do|roto|doblado)|planta[s]?\s*ca[ií]da",
        "daño mecánico / viento",
        "low",
        "Coloque tutores o estacas para sostener las plantas caídas. "
        "Aplique tierra en la base del tallo para mayor soporte. "
        "Pode las partes rotas con herramienta limpia y desinfectada.",
    ),
]

# ---------------------------------------------------------------------------
# Crop keyword map — (regex, crop_name)
# ---------------------------------------------------------------------------
_CROP_PATTERNS: list[tuple[str, str]] = [
    (r"ma[ií]z|milpa|elote|mazorca", "maiz"),
    (r"frijol(es)?", "frijol"),
    (r"agave|maguey|mezcal", "agave"),
    (r"tomate|jitomate", "tomate"),
    (r"chile[s]?|jalapeño|habanero|serrano", "chile"),
    (r"nopal(es)?|tuna[s]?", "nopal"),
    (r"limón|limon|lima[s]?", "limon"),
    (r"mango[s]?", "mango"),
    (r"caf[eé]|cafeto[s]?", "cafe"),
    (r"aguacate[s]?|palta[s]?", "aguacate"),
    (r"calabaz[ao]|calabacita", "calabaza"),
    (r"trigo", "trigo"),
    (r"soya|soja", "soya"),
    (r"manzana[s]?|manzano[s]?", "manzana"),
    (r"uva[s]?|vid|viñedo", "uva"),
]

_DEFAULT_RESPONSE = (
    "problema agrícola no identificado",
    "low",
    "Describa con más detalle los síntomas visibles en sus plantas "
    "(color de hojas, forma del daño, parte afectada). "
    "Mientras tanto, revise el nivel de humedad del suelo y la presencia de insectos.",
)


def _detect_crop(text: str) -> str | None:
    lower = text.lower()
    for pattern, crop in _CROP_PATTERNS:
        if re.search(pattern, lower):
            return crop
    return None


def _detect_issue(text: str) -> tuple[str, str, str]:
    """Return (issue_label, severity, recommended_action_es)."""
    lower = text.lower()
    for pattern, issue, severity, action in _ISSUE_PATTERNS:
        if re.search(pattern, lower):
            return issue, severity, action
    return _DEFAULT_RESPONSE


def _confidence(issue_label: str, crop: str | None) -> float:
    """Higher confidence when both issue and crop are clearly detected."""
    if issue_label == _DEFAULT_RESPONSE[0]:
        return 0.35
    base = 0.72
    if crop:
        base += 0.15
    return round(min(base, 0.97), 2)


def simulate_farmer_query(message: str, crop_hint: str | None = None) -> dict:
    """Simulate a WhatsApp AI response to a Spanish farming query.

    Args:
        message: Raw Spanish text from the farmer.
        crop_hint: Crop type from farm DB (used as fallback if not in message).

    Returns:
        dict with keys: detected_issue, crop, severity, recommended_action, confidence.
    """
    detected_crop = _detect_crop(message) or crop_hint
    issue, severity, action = _detect_issue(message)
    confidence = _confidence(issue, detected_crop)

    return {
        "detected_issue": issue,
        "crop": detected_crop,
        "severity": severity,
        "recommended_action": action,
        "confidence": confidence,
    }
