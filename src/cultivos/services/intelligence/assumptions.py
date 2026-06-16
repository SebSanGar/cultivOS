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
    # ----------------------------------------- Risk avoided per treatment
    "risk_per_treatment_mxn": AssumptionRecord(
        value=3_000.0,
        low=1_500.0,
        high=5_000.0,
        unit="MXN/treatment",
        source_name="SARE Louisiana — Precision N management (cotton/corn equal yield at 50% less N)",
        source_url="https://www.sare.org/publications/managing-cover-crops-profitably/",
        source_year=2021,
        status="model_assumption",
        confidence_note=(
            "Early-intervention crop loss prevention estimate per timely treatment. "
            "SARE studies show precision application prevents 15-25% yield loss risk. "
            "At $21,330/ha maize (Unisem 2025), preventing 15% loss on 1 ha ≈ $3,200. "
            "Low = 0.5×, high = 1.7×. Do not present as a measured result."
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
    # ===================== Ontario / Canada (CAD) — Canada-first market =====================
    # Ontario field crops (corn/soy/wheat) are RAINFED — no irrigation/water lever.
    "water_savings_per_ha_ca": AssumptionRecord(
        value=0.0,
        low=0.0,
        high=0.0,
        unit="CAD/ha/yr",
        source_name="OMAFRA agronomy — Ontario field crops are predominantly rainfed",
        source_url="https://www.ontario.ca/page/agriculture-and-food",
        source_year=2025,
        status="model_assumption",
        confidence_note=(
            "Ontario corn/soybean/wheat are rainfed; precision irrigation/water "
            "savings is NOT a lever here (unlike Jalisco). Set to 0 deliberately."
        ),
    ),
    "fertilizer_savings_per_ha_ca": AssumptionRecord(
        value=96.0,
        low=48.0,
        high=120.0,
        unit="CAD/ha/yr",
        source_name="OMAFRA Publication 60 Field Crop Budgets 2025 + Lan & Ban 2025 PA meta-analysis (85 studies)",
        source_url="https://www.ontario.ca/files/2025-01/omafa-field-crop-budgets-pub-60-en-2025-01-14.pdf",
        source_year=2025,
        status="literature",
        confidence_note=(
            "Targeted-input (fertilizer + crop protection) savings. Blended Ontario "
            "targeted inputs ~CAD 479/ha (corn 597, soy 376, wheat 465; OMAFRA Pub 60 "
            "2025, $/ac x 2.471). PA savings 10-25% (Lan & Ban 2025 meta: NUE +15%, "
            "pesticide -13% — GENERAL, not Ontario-specific). value=20%x479; low=10%, "
            "high=25%. Soybean fixes its own N, lowering the blended lever — conservative."
        ),
    ),
    "yield_baseline_per_ha_ca": AssumptionRecord(
        value=67.0,
        low=45.0,
        high=111.0,
        unit="CAD/ha/yr",
        source_name="StatCan 2024 Ontario yields + Grain Farmers of Ontario 2025 cash prices",
        source_url="https://www150.statcan.gc.ca/n1/daily-quotidien/241205/dq241205b-eng.htm",
        source_year=2024,
        status="literature",
        confidence_note=(
            "Yield protected by early NDVI detection. Blended gross yield ~CAD 2,227/ha "
            "(corn 11.3 t x $252, soy 3.49 t x $585, wheat 6.2 t x $289; StatCan 2024 "
            "yields, GFO Apr-2025 prices). Protect ~3% via timely intervention -> 67/ha; "
            "low 2%, high 5%. Conservative; not an Ontario PA field trial."
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
