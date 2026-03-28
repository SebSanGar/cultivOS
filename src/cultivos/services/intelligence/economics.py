"""Pure economic impact calculator — data in, savings out. No HTTP, no DB, no side effects.

Estimates annual savings in MXN from precision agriculture adoption.
Based on cultivOS baseline: $414,000 MXN saved per farm/year for a typical 20ha Jalisco operation.

Savings categories:
- Water: reduced waste through precision irrigation (CONAGUA: 57% wasted by inefficiency)
- Fertilizer: targeted organic treatments vs. blanket application
- Yield: health-driven improvements from early intervention
"""

from typing import TypedDict


# Baseline savings per hectare per year (MXN) — derived from $414,000 / 20ha reference farm
# Broken down by savings category based on precision ag literature for small Mexican farms
WATER_SAVINGS_PER_HA = 8_000.0      # ~$8,000 MXN/ha/yr from irrigation optimization
FERTILIZER_SAVINGS_PER_HA = 5_000.0  # ~$5,000 MXN/ha/yr from targeted organic treatments
YIELD_BASELINE_PER_HA = 7_700.0     # ~$7,700 MXN/ha/yr from early intervention yield gains
# Total: ~$20,700 MXN/ha/yr * 20ha = ~$414,000 MXN/yr (matches reference metric)

# Default irrigation efficiency for farms without sensor data
DEFAULT_IRRIGATION_EFFICIENCY = 0.43  # CONAGUA average (1 - 0.57 waste)


class EconomicImpactResult(TypedDict):
    water_savings_mxn: int
    fertilizer_savings_mxn: int
    yield_improvement_mxn: int
    total_savings_mxn: int
    nota: str


def calculate_farm_savings(
    health_score: float,
    hectares: float,
    treatment_count: int,
    irrigation_efficiency: float | None,
) -> EconomicImpactResult:
    """Calculate estimated annual savings from precision agriculture.

    Args:
        health_score: 0-100 composite health score (avg across fields).
        hectares: Total farm area in hectares.
        treatment_count: Number of treatments applied (more = better fertilizer targeting).
        irrigation_efficiency: 0-1 ratio (None = use CONAGUA default 0.43).

    Returns:
        EconomicImpactResult with per-category and total savings in MXN.
    """
    if hectares <= 0:
        return EconomicImpactResult(
            water_savings_mxn=0,
            fertilizer_savings_mxn=0,
            yield_improvement_mxn=0,
            total_savings_mxn=0,
            nota="Sin hectareas registradas — no se puede estimar impacto economico.",
        )

    clamped_health = max(0.0, min(100.0, health_score))

    # --- Water savings ---
    # Higher improvement when current efficiency is low (more room to optimize)
    eff = irrigation_efficiency if irrigation_efficiency is not None else DEFAULT_IRRIGATION_EFFICIENCY
    eff = max(0.0, min(1.0, eff))
    # Potential improvement: gap between current and optimal (0.90 target)
    water_improvement_factor = max(0.0, 0.90 - eff)
    # Scale by health: healthier farm = better data = better optimization
    water_multiplier = (clamped_health / 100.0) * (water_improvement_factor / 0.47)  # normalize to CONAGUA gap
    water_savings = round(WATER_SAVINGS_PER_HA * hectares * water_multiplier)

    # --- Fertilizer savings ---
    # More treatments = more data = better targeting = more savings
    treatment_factor = min(1.0, treatment_count / 6.0)  # 6+ treatments = full benefit
    # Health score indicates soil understanding
    fert_multiplier = (clamped_health / 100.0) * (0.3 + 0.7 * treatment_factor)
    fertilizer_savings = round(FERTILIZER_SAVINGS_PER_HA * hectares * fert_multiplier)

    # --- Yield improvement ---
    # Higher health = more yield captured vs. potential
    yield_multiplier = clamped_health / 100.0
    yield_savings = round(YIELD_BASELINE_PER_HA * hectares * yield_multiplier)

    total = water_savings + fertilizer_savings + yield_savings

    # Generate note
    if total >= 300_000:
        nota = f"Impacto economico significativo: ${total:,} MXN/ano estimado. La agricultura de precision esta generando valor real."
    elif total >= 100_000:
        nota = f"Ahorro estimado de ${total:,} MXN/ano. Mejoras en riego y salud del campo pueden incrementar este valor."
    else:
        nota = f"Ahorro estimado de ${total:,} MXN/ano. Con mas datos y tratamientos, el impacto economico crecera."

    return EconomicImpactResult(
        water_savings_mxn=water_savings,
        fertilizer_savings_mxn=fertilizer_savings,
        yield_improvement_mxn=yield_savings,
        total_savings_mxn=total,
        nota=nota,
    )
