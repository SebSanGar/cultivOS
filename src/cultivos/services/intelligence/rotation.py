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
