"""Provenance registry for all magic numbers used in cultivOS impact calculations.

Each record documents a constant's value, uncertainty range, source, and status.

Statuses:
  measured         — derived from real sensor/DB data for this farm
  literature       — published study or government statistic
  model_assumption — internal estimate or heuristic (label as such in UI)
"""

from typing import Literal, TypedDict


Status = Literal["measured", "literature", "model_assumption"]


class AssumptionRecord(TypedDict):
    value: float
    low: float
    high: float
    unit: str
    source_name: str
    source_url: str
    source_year: int
    status: Status
    confidence_note: str


REGISTRY: dict[str, AssumptionRecord] = {
    # ------------------------------------------------------------------ Water
    "water_savings_per_ha": AssumptionRecord(
        value=8_000.0,
        low=4_800.0,
        high=8_000.0,
        unit="MXN/ha/yr",
        source_name="MDPI Agronomy — Precision Agriculture Meta-Analysis (85 studies)",
        source_url="https://www.mdpi.com/2073-4395/15/3/123",
        source_year=2025,
        status="model_assumption",
        confidence_note=(
            "Derived from $414K/20ha reference farm breakdown. "
            "Precision scheduling typically 20-30% less water (low confidence). "
            "Low = 0.6×, high = point estimate."
        ),
    ),
    # -------------------------------------------------------------- Fertilizer
    "fertilizer_savings_per_ha": AssumptionRecord(
        value=5_000.0,
        low=3_000.0,
        high=5_000.0,
        unit="MXN/ha/yr",
        source_name="MDPI Agronomy — Precision Agriculture Meta-Analysis (85 studies)",
        source_url="https://www.mdpi.com/2073-4395/15/3/123",
        source_year=2025,
        status="model_assumption",
        confidence_note=(
            "Derived from $414K/20ha reference farm breakdown. "
            "Input savings 8-20% per MDPI 2025. "
            "Low = 0.6×, high = point estimate."
        ),
    ),
    # ------------------------------------------------------------------ Yield
    "yield_baseline_per_ha": AssumptionRecord(
        value=7_700.0,
        low=4_620.0,
        high=7_700.0,
        unit="MXN/ha/yr",
        source_name="MDPI Agronomy — Precision Agriculture Yield Review",
        source_url="https://www.mdpi.com/2073-4395/16/1/45",
        source_year=2026,
        status="model_assumption",
        confidence_note=(
            "Derived from $414K/20ha reference farm breakdown. "
            "Precision-ag yield gain +2-6% per MDPI 2026 systematic review. "
            "Low = 0.6×, high = point estimate."
        ),
    ),
    # ----------------------------------------------- Irrigation efficiency
    "default_irrigation_efficiency": AssumptionRecord(
        value=0.43,
        low=0.30,
        high=0.55,
        unit="ratio (0–1)",
        source_name="CONAGUA — Estadisticas del Agua en Mexico 2017-2018",
        source_url="https://www.gob.mx/conagua/documentos/estadisticas-del-agua-en-mexico",
        source_year=2018,
        status="literature",
        confidence_note=(
            "CONAGUA reports ~57% inefficiency (1 - 0.57 = 0.43 efficiency). "
            "Range reflects regional variation across Jalisco municipalities."
        ),
    ),
    # ------------------------------------------------ Subscription tier rates
    "tier_rate_basic_mxn_ha": AssumptionRecord(
        value=3_600.0,
        low=3_600.0,
        high=3_600.0,
        unit="MXN/ha/yr",
        source_name="cultivOS pricing model (internal)",
        source_url="https://github.com/cultivOS/cultivOS",
        source_year=2026,
        status="model_assumption",
        confidence_note="Basic tier subscription rate per hectare per year (MXN).",
    ),
    "tier_rate_standard_mxn_ha": AssumptionRecord(
        value=5_400.0,
        low=5_400.0,
        high=5_400.0,
        unit="MXN/ha/yr",
        source_name="cultivOS pricing model (internal)",
        source_url="https://github.com/cultivOS/cultivOS",
        source_year=2026,
        status="model_assumption",
        confidence_note="Standard tier subscription rate per hectare per year (MXN).",
    ),
    # ----------------------------------------- Carbon accounting constants
    "soc_to_co2e": AssumptionRecord(
        value=3.67,
        low=3.67,
        high=3.67,
        unit="tCO2e/tC",
        source_name="IPCC Guidelines for National Greenhouse Gas Inventories (2006) — Vol 4 Agriculture",
        source_url="https://www.ipcc-nggip.iges.or.jp/public/2006gl/vol4.html",
        source_year=2006,
        status="literature",
        confidence_note=(
            "Molecular weight ratio CO2/C = 44/12 ≈ 3.667. Used to convert soil organic carbon "
            "(SOC) tonnes to CO2-equivalent tonnes for carbon sequestration reporting. "
            "Universally accepted scientific constant; value does not vary by region."
        ),
    ),
    # ----------------------------------------- Per-treatment savings heuristic
    "per_treatment_savings_mxn": AssumptionRecord(
        value=1_500.0,
        low=900.0,
        high=1_500.0,
        unit="MXN/treatment",
        source_name="cultivOS internal model assumption",
        source_url="https://github.com/cultivOS/cultivOS",
        source_year=2026,
        status="model_assumption",
        confidence_note=(
            "Rough heuristic: prevention vs reactive intervention cost. "
            "Not based on a published study. Do not use as a point estimate in investor materials."
        ),
    ),
}


def get(key: str) -> AssumptionRecord:
    """Return the assumption record for a key. Raises KeyError if not found."""
    if key not in REGISTRY:
        raise KeyError(f"No assumption registered for key '{key}'")
    return REGISTRY[key]


def get_value(key: str) -> float:
    """Return the central value for a key. Raises KeyError if not found."""
    return get(key)["value"]
