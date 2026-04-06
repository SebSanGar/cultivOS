"""Pure crop rotation planner — data in, rotation plan out.

No HTTP, no DB, no side effects. Regenerative-first: prioritizes
nitrogen fixation, cover cropping, and soil health recovery.

Jalisco seasons:
- temporal (rainy): June-October — main growing season
- secas (dry): November-May — limited water, drought-tolerant crops or cover crops
- transicion: transition period between seasons
"""

from typing import TypedDict


class SoilInput(TypedDict, total=False):
    organic_matter_pct: float | None
    nitrogen_ppm: float | None
    ph: float | None


class RotationEntry(TypedDict):
    season: str        # temporal, secas, transicion
    crop: str          # crop name in Spanish
    reason: str        # why this crop in this slot (Spanish)
    purpose: str       # nitrogen fixation, cash crop, cover crop, etc.
    months: str        # approximate month range


class MultiYearEntry(TypedDict):
    year: int                  # 1, 2, or 3
    season: str
    crop: str
    reason: str
    purpose: str
    months: str
    organic_matter_pct: float  # projected soil OM after this season


class MultiYearResult(TypedDict):
    plan: list[MultiYearEntry]
    total_years: int
    milpa_recommended: bool
    milpa_description: str
    om_start: float
    om_end: float


# Crops that fix nitrogen (legumes)
_LEGUMES = {"frijol", "lenteja", "haba", "veza", "garbanzo"}

# Heavy feeders that deplete nitrogen
_HEAVY_FEEDERS = {"maiz", "sorgo", "calabaza", "chile", "tomate", "aguacate"}

# Cover crops for soil recovery
_COVER_CROPS = {"veza", "trebol", "centeno", "avena"}

# Jalisco-appropriate crop rotations after each crop type
_ROTATION_AFTER: dict[str, list[str]] = {
    "maiz": ["frijol", "calabaza", "veza"],
    "frijol": ["maiz", "sorgo", "calabaza"],
    "sorgo": ["frijol", "garbanzo", "veza"],
    "calabaza": ["frijol", "maiz", "avena"],
    "agave": ["frijol", "maiz", "calabaza"],
    "aguacate": ["frijol", "veza", "trebol"],
    "chile": ["frijol", "maiz", "veza"],
    "tomate": ["frijol", "maiz", "avena"],
    "garbanzo": ["maiz", "sorgo", "calabaza"],
}

_DEFAULT_ROTATION = ["frijol", "maiz", "calabaza"]


def _needs_cover_crop(soil: SoilInput | None) -> bool:
    """Check if soil health is degraded enough to warrant a cover crop."""
    if not soil:
        return False
    om = soil.get("organic_matter_pct")
    n = soil.get("nitrogen_ppm")
    if om is not None and om < 2.0:
        return True
    if n is not None and n < 10:
        return True
    return False


def _needs_nitrogen_fix(last_crop: str, soil: SoilInput | None) -> bool:
    """Check if field needs nitrogen fixation from a legume."""
    if last_crop in _HEAVY_FEEDERS:
        return True
    if soil:
        n = soil.get("nitrogen_ppm")
        if n is not None and n < 15:
            return True
    return False


def plan_rotation(
    last_crop: str,
    region: str = "jalisco",
    soil: SoilInput | None = None,
) -> list[RotationEntry]:
    """Generate a 3-season crop rotation plan.

    Args:
        last_crop: The crop most recently grown (Spanish name, lowercase).
        region: Growing region (currently only 'jalisco' supported).
        soil: Optional soil analysis data to inform cover crop decisions.

    Returns:
        List of 3+ RotationEntry dicts representing the next seasons.
    """
    last_crop = last_crop.lower().strip()
    plan: list[RotationEntry] = []

    # Get candidate crops for rotation
    candidates = _ROTATION_AFTER.get(last_crop, _DEFAULT_ROTATION)

    needs_cover = _needs_cover_crop(soil)
    needs_legume = _needs_nitrogen_fix(last_crop, soil)

    # Season 1: secas (dry season) — cover crop or legume
    if needs_cover:
        plan.append(RotationEntry(
            season="secas",
            crop="veza",
            reason="Suelo con materia organica baja — cultivo de cobertura para recuperar estructura y nutrientes",
            purpose="cobertura / abono verde",
            months="Nov-Feb",
        ))
    elif needs_legume:
        # Pick first legume from candidates, or default to frijol
        legume = next((c for c in candidates if c in _LEGUMES), "frijol")
        plan.append(RotationEntry(
            season="secas",
            crop=legume,
            reason=f"Despues de {last_crop} (alto consumo de nitrogeno) — leguminosa para fijar N",
            purpose="fijacion de nitrogeno",
            months="Nov-Feb",
        ))
    else:
        # Default: first candidate that's different from last crop
        crop = next((c for c in candidates if c != last_crop), candidates[0])
        plan.append(RotationEntry(
            season="secas",
            crop=crop,
            reason=f"Rotacion despues de {last_crop} para romper ciclos de plagas y enfermedades",
            purpose="diversificacion",
            months="Nov-Feb",
        ))

    # Season 2: temporal (rainy season) — main cash crop
    prev_crop = plan[-1]["crop"]
    if prev_crop in _LEGUMES:
        # After legume, plant heavy feeder to use fixed nitrogen
        cash = next(
            (c for c in ["maiz", "sorgo", "calabaza"] if c != last_crop),
            "maiz",
        )
        plan.append(RotationEntry(
            season="temporal",
            crop=cash,
            reason=f"Temporal con suelo enriquecido por {prev_crop} — aprovechar nitrogeno fijado",
            purpose="cultivo principal",
            months="Jun-Oct",
        ))
    elif prev_crop in _COVER_CROPS:
        # After cover crop, plant cash crop
        cash = next((c for c in candidates if c not in _COVER_CROPS), "maiz")
        plan.append(RotationEntry(
            season="temporal",
            crop=cash,
            reason=f"Suelo recuperado con {prev_crop} — temporada ideal para cultivo principal",
            purpose="cultivo principal",
            months="Jun-Oct",
        ))
    else:
        # Rotate to something different
        crop = next(
            (c for c in _DEFAULT_ROTATION if c != prev_crop and c != last_crop),
            "maiz",
        )
        plan.append(RotationEntry(
            season="temporal",
            crop=crop,
            reason=f"Rotacion para diversificar despues de {prev_crop}",
            purpose="cultivo principal",
            months="Jun-Oct",
        ))

    # Season 3: secas again — recovery or prep
    prev_crop2 = plan[-1]["crop"]
    if prev_crop2 in _HEAVY_FEEDERS:
        # After heavy feeder, legume
        legume = next((c for c in _LEGUMES if c != plan[0]["crop"]), "frijol")
        plan.append(RotationEntry(
            season="secas",
            crop=legume,
            reason=f"Restablecer nitrogeno despues de {prev_crop2} — preparar suelo para siguiente temporal",
            purpose="fijacion de nitrogeno",
            months="Nov-Feb",
        ))
    else:
        # After legume/light crop, can do another cash crop or cover
        plan.append(RotationEntry(
            season="secas",
            crop="avena",
            reason="Cobertura invernal para proteger suelo y suprimir malezas",
            purpose="cobertura / abono verde",
            months="Nov-Feb",
        ))

    return plan


# -- Multi-year rotation planner -----------------------------------------------

# Milpa crops: the Three Sisters polyculture (3,500+ years in Mesoamerica)
_MILPA_CROPS = {"maiz", "frijol", "calabaza"}

# Crops compatible with milpa system (annuals that rotate well with the three sisters)
_MILPA_COMPATIBLE = {"maiz", "frijol", "calabaza", "sorgo", "chile", "tomate"}

# Perennials where milpa doesn't apply
_PERENNIALS = {"aguacate", "agave"}

# Soil OM change per crop type (percentage points per season)
_OM_DELTA: dict[str, float] = {
    # Cover crops / legumes increase OM
    "veza": +0.25,
    "trebol": +0.20,
    "centeno": +0.15,
    "avena": +0.15,
    "frijol": +0.10,
    "garbanzo": +0.10,
    "lenteja": +0.10,
    "haba": +0.10,
    # Cash crops slightly decrease OM
    "maiz": -0.10,
    "sorgo": -0.10,
    "calabaza": -0.05,
    "chile": -0.05,
    "tomate": -0.10,
    "aguacate": -0.05,
    "agave": 0.0,
}

_DEFAULT_OM_START = 2.5  # assumed if no soil data


def _is_milpa_candidate(last_crop: str, region: str) -> bool:
    """Check if milpa system is appropriate for this crop/region."""
    if last_crop in _PERENNIALS:
        return False
    if last_crop in _MILPA_COMPATIBLE:
        return True
    return False


def _project_om(current_om: float, crop: str) -> float:
    """Project soil organic matter after growing a crop for one season."""
    delta = _OM_DELTA.get(crop, 0.0)
    projected = current_om + delta
    # OM can't go below 0.5% or above 8%
    return round(max(0.5, min(8.0, projected)), 2)


def plan_multi_year_rotation(
    last_crop: str,
    region: str = "jalisco",
    soil: SoilInput | None = None,
) -> MultiYearResult:
    """Generate a 3-year (6-season) crop rotation plan with soil OM projections.

    Includes milpa (Three Sisters) recommendations for Jalisco
    and projects soil organic matter recovery across the plan.

    Args:
        last_crop: The crop most recently grown (Spanish name, lowercase).
        region: Growing region (currently only 'jalisco' supported).
        soil: Optional soil analysis data to inform cover crop decisions.

    Returns:
        MultiYearResult with 6-season plan, milpa info, and OM projections.
    """
    last_crop = last_crop.lower().strip()
    om_start = (soil or {}).get("organic_matter_pct") or _DEFAULT_OM_START
    current_om = om_start
    plan: list[MultiYearEntry] = []

    milpa = _is_milpa_candidate(last_crop, region)
    prev_crop = last_crop

    for year in range(1, 4):
        # --- Secas (dry season) ---
        secas_crop = _pick_secas_crop(prev_crop, soil, current_om, year, milpa)
        current_om = _project_om(current_om, secas_crop["crop"])
        plan.append(MultiYearEntry(
            year=year,
            season="secas",
            crop=secas_crop["crop"],
            reason=secas_crop["reason"],
            purpose=secas_crop["purpose"],
            months="Nov-Feb",
            organic_matter_pct=current_om,
        ))

        # --- Temporal (rainy season) ---
        temporal_crop = _pick_temporal_crop(
            plan[-1]["crop"], prev_crop, current_om, year, milpa,
        )
        current_om = _project_om(current_om, temporal_crop["crop"])
        plan.append(MultiYearEntry(
            year=year,
            season="temporal",
            crop=temporal_crop["crop"],
            reason=temporal_crop["reason"],
            purpose=temporal_crop["purpose"],
            months="Jun-Oct",
            organic_matter_pct=current_om,
        ))

        prev_crop = plan[-1]["crop"]

    milpa_desc = ""
    if milpa:
        milpa_desc = (
            "Sistema milpa recomendado: policultivo ancestral de maiz + frijol + calabaza. "
            "Tradicion de 3,500+ anos en Mesoamerica. El frijol fija nitrogeno, "
            "la calabaza retiene humedad y suprime malezas, el maiz provee estructura vertical."
        )

    return MultiYearResult(
        plan=plan,
        total_years=3,
        milpa_recommended=milpa,
        milpa_description=milpa_desc,
        om_start=round(om_start, 2),
        om_end=round(current_om, 2),
    )


def _pick_secas_crop(
    prev_crop: str,
    soil: SoilInput | None,
    current_om: float,
    year: int,
    milpa: bool,
) -> dict:
    """Pick the dry-season crop based on soil health and rotation history."""
    needs_cover = current_om < 2.0
    needs_legume = prev_crop in _HEAVY_FEEDERS or (
        soil and (soil.get("nitrogen_ppm") or 99) < 15
    )

    if needs_cover:
        return {
            "crop": "veza",
            "reason": f"Ano {year}: suelo con materia organica baja ({current_om}%) — "
                      "cultivo de cobertura para recuperar estructura",
            "purpose": "cobertura / abono verde",
        }
    elif needs_legume:
        # In milpa system, prefer frijol
        legume = "frijol" if milpa else next(
            (c for c in _ROTATION_AFTER.get(prev_crop, _DEFAULT_ROTATION) if c in _LEGUMES),
            "frijol",
        )
        return {
            "crop": legume,
            "reason": f"Ano {year}: fijacion de nitrogeno despues de {prev_crop} — "
                      "preparar suelo para temporal",
            "purpose": "fijacion de nitrogeno",
        }
    else:
        # Light crop or cover to maintain soil
        crop = "avena" if year % 2 == 0 else "frijol"
        return {
            "crop": crop,
            "reason": f"Ano {year}: rotacion para diversificar y mantener salud del suelo",
            "purpose": "diversificacion" if crop not in _LEGUMES else "fijacion de nitrogeno",
        }


def _pick_temporal_crop(
    secas_crop: str,
    original_last_crop: str,
    current_om: float,
    year: int,
    milpa: bool,
) -> dict:
    """Pick the rainy-season (main) crop based on what was planted in secas."""
    if milpa:
        # Rotate through milpa crops across years
        milpa_sequence = ["maiz", "calabaza", "maiz"]
        cash = milpa_sequence[(year - 1) % 3]
        if cash == original_last_crop and year == 1:
            cash = "calabaza"
        return {
            "crop": cash,
            "reason": f"Ano {year}: sistema milpa — {cash} como cultivo principal "
                      f"despues de {secas_crop} (suelo enriquecido)",
            "purpose": "cultivo principal (milpa)",
        }

    if secas_crop in _LEGUMES:
        cash = next(
            (c for c in ["maiz", "sorgo", "calabaza"] if c != original_last_crop),
            "maiz",
        )
        return {
            "crop": cash,
            "reason": f"Ano {year}: suelo enriquecido por {secas_crop} — "
                      "aprovechar nitrogeno fijado",
            "purpose": "cultivo principal",
        }

    if secas_crop in _COVER_CROPS:
        candidates = _ROTATION_AFTER.get(original_last_crop, _DEFAULT_ROTATION)
        cash = next((c for c in candidates if c not in _COVER_CROPS), "maiz")
        return {
            "crop": cash,
            "reason": f"Ano {year}: suelo recuperado con {secas_crop} — "
                      "temporada ideal para cultivo principal",
            "purpose": "cultivo principal",
        }

    crop = next(
        (c for c in _DEFAULT_ROTATION if c != secas_crop and c != original_last_crop),
        "maiz",
    )
    return {
        "crop": crop,
        "reason": f"Ano {year}: rotacion para diversificar despues de {secas_crop}",
        "purpose": "cultivo principal",
    }
