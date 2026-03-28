"""Pure region metadata resolver — farm location to agricultural profile.

Maps farm state/country to region-specific agricultural context: climate zone,
soil type, growing season, key crops, currency, and seasonal notes.
Used by the recommendation engine to inject region-calibrated advice.

No HTTP, no DB, no side effects. Based on AgriRegion (arxiv 2512.10114)
region-aware RAG pattern.
"""

from typing import TypedDict


class RegionProfile(TypedDict):
    region_name: str
    climate_zone: str
    soil_type: str
    growing_season: str
    key_crops: list[str]
    currency: str
    seasonal_notes: str


# MXN to CAD approximate conversion factor for cost estimates
MXN_TO_CAD = 0.075


_PROFILES: dict[str, RegionProfile] = {
    "jalisco_mx": RegionProfile(
        region_name="jalisco",
        climate_zone="tropical_subtropical",
        soil_type="Suelos volcanicos (andosoles) — alta retencion de fosforo, buen drenaje",
        growing_season="Temporal Jun-Oct / Secas Nov-May",
        key_crops=["maiz", "agave", "berries", "aguacate", "cana", "jitomate"],
        currency="MXN",
        seasonal_notes="Lluvias intensas Jun-Sep, sequia Nov-Abr. Riesgo de heladas en Altos de Jalisco Dic-Feb.",
    ),
    "ontario_ca": RegionProfile(
        region_name="ontario",
        climate_zone="temperate_continental",
        soil_type="Glacial till soils — arcillosos a franco-arcillosos, alta fertilidad natural",
        growing_season="May-Sep (short growing season, frost-free ~140 days)",
        key_crops=["corn", "soy", "wheat", "greenhouse", "apples", "grapes"],
        currency="CAD",
        seasonal_notes="Frost risk before May and after Sep. Short window for field applications. Snow cover benefits soil biology Dec-Mar.",
    ),
}

_GENERIC = RegionProfile(
    region_name="generic",
    climate_zone="generic",
    soil_type="Variable — realizar analisis de suelo local",
    growing_season="Variable segun latitud y altitud",
    key_crops=["maiz", "frijol", "hortalizas"],
    currency="MXN",
    seasonal_notes="Consultar condiciones climaticas locales antes de aplicar tratamientos.",
)


def get_region_profile(
    state: str = "Jalisco",
    country: str = "MX",
) -> RegionProfile:
    """Resolve farm location to agricultural region profile.

    Pure function — no DB, no HTTP.

    Args:
        state: Farm state/province (e.g. "Jalisco", "Ontario")
        country: ISO country code (e.g. "MX", "CA")

    Returns:
        RegionProfile with climate, soil, season, crops, currency, notes.
        Falls back to generic profile for unrecognized regions.
    """
    key = f"{state.lower().strip()}_{country.lower().strip()}"
    return _PROFILES.get(key, _GENERIC)
