"""Pure soil carbon estimation — data in, results out. No HTTP, no DB, no side effects.

Estimates soil organic carbon (SOC) from organic matter percentage using the
Van Bemmelen factor (0.58). Provides trend detection across multiple soil records
and regenerative practice recommendations for carbon-losing fields.

MRV-lite: Monitoring, Reporting, Verification at zero marginal cost from existing
soil analysis data.
"""

from typing import TypedDict


# Van Bemmelen factor: organic matter × 0.58 = soil organic carbon
VAN_BEMMELEN = 0.58

# Default bulk density (g/cm³) for agricultural soil when not measured
DEFAULT_BULK_DENSITY = 1.3

# SOC classification thresholds (% SOC)
SOC_BAJO = 1.0       # < 1% SOC = low carbon
SOC_ADECUADO = 2.0   # 1-3% SOC = adequate
# > 3% = high

# Trend detection: minimum absolute change in SOC t/ha to count as gaining/losing
TREND_THRESHOLD_TONNES = 2.0  # ±2 t/ha considered stable


class SOCEstimate(TypedDict):
    organic_matter_pct: float
    soc_pct: float
    soc_tonnes_per_ha: float
    depth_cm: float
    bulk_density: float
    clasificacion: str  # bajo, adecuado, alto


class CarbonTrendResult(TypedDict):
    tendencia: str  # ganando, estable, perdiendo, datos_insuficientes
    cambio_soc_tonnes_per_ha: float
    registros: int
    primer_soc_tonnes_per_ha: float
    ultimo_soc_tonnes_per_ha: float
    recomendaciones: list[str]


def estimate_soc(
    organic_matter_pct: float,
    depth_cm: float,
    bulk_density: float = DEFAULT_BULK_DENSITY,
) -> SOCEstimate:
    """Estimate soil organic carbon from organic matter percentage.

    Formula: SOC (t/ha) = SOC% / 100 × depth(m) × bulk_density(g/cm³) × 10000
    SOC% = OM% × Van Bemmelen factor (0.58)

    Args:
        organic_matter_pct: Organic matter content (%)
        depth_cm: Sampling depth in centimeters
        bulk_density: Soil bulk density (g/cm³), default 1.3

    Returns:
        SOCEstimate with carbon percentage, tonnes/ha, and classification.
    """
    soc_pct = round(organic_matter_pct * VAN_BEMMELEN, 4)
    depth_m = depth_cm / 100.0
    soc_tonnes_per_ha = round(soc_pct / 100.0 * depth_m * bulk_density * 10000, 2)

    if soc_pct < SOC_BAJO:
        clasificacion = "bajo"
    elif soc_pct < SOC_ADECUADO:
        clasificacion = "adecuado"
    else:
        clasificacion = "alto"

    return SOCEstimate(
        organic_matter_pct=organic_matter_pct,
        soc_pct=soc_pct,
        soc_tonnes_per_ha=soc_tonnes_per_ha,
        depth_cm=depth_cm,
        bulk_density=bulk_density,
        clasificacion=clasificacion,
    )


def compute_carbon_trend(
    records: list[dict],
) -> CarbonTrendResult:
    """Compute carbon sequestration trend from soil analysis history.

    Requires 3+ records sorted by date for meaningful trend detection.
    Compares first and last SOC estimates.

    Args:
        records: List of dicts with organic_matter_pct, depth_cm, sampled_at keys,
                 chronologically ordered.

    Returns:
        CarbonTrendResult with trend direction, change, and recommendations.
    """
    if len(records) < 3:
        return CarbonTrendResult(
            tendencia="datos_insuficientes",
            cambio_soc_tonnes_per_ha=0.0,
            registros=len(records),
            primer_soc_tonnes_per_ha=0.0,
            ultimo_soc_tonnes_per_ha=0.0,
            recomendaciones=[],
        )

    # Sort by sampled_at to ensure chronological order
    sorted_records = sorted(records, key=lambda r: r["sampled_at"])

    first = sorted_records[0]
    last = sorted_records[-1]

    first_soc = estimate_soc(
        organic_matter_pct=first["organic_matter_pct"],
        depth_cm=first.get("depth_cm", 30.0),
    )
    last_soc = estimate_soc(
        organic_matter_pct=last["organic_matter_pct"],
        depth_cm=last.get("depth_cm", 30.0),
    )

    cambio = round(last_soc["soc_tonnes_per_ha"] - first_soc["soc_tonnes_per_ha"], 2)

    if cambio > TREND_THRESHOLD_TONNES:
        tendencia = "ganando"
    elif cambio < -TREND_THRESHOLD_TONNES:
        tendencia = "perdiendo"
    else:
        tendencia = "estable"

    recomendaciones: list[str] = []
    if tendencia == "perdiendo":
        recomendaciones = [
            "Incorporar abonos verdes (leguminosas) para fijar carbono en el suelo",
            "Aplicar composta o bocashi regularmente (5-10 ton/ha por ciclo)",
            "Reducir labranza — considerar labranza cero o minima",
            "Mantener cobertura vegetal permanente entre ciclos",
            "Evitar quema de rastrojo — incorporar residuos al suelo",
        ]
    elif tendencia == "estable":
        recomendaciones = [
            "Mantener practicas actuales de manejo de suelo",
            "Considerar abonos verdes para incrementar carbono gradualmente",
        ]

    return CarbonTrendResult(
        tendencia=tendencia,
        cambio_soc_tonnes_per_ha=cambio,
        registros=len(records),
        primer_soc_tonnes_per_ha=first_soc["soc_tonnes_per_ha"],
        ultimo_soc_tonnes_per_ha=last_soc["soc_tonnes_per_ha"],
        recomendaciones=recomendaciones,
    )
