"""Pure yield prediction — data in, prediction out. No HTTP, no DB, no side effects.

Estimates harvest kg/ha based on crop type, field area, and health score.
Uses Jalisco-specific baseline yields from SIAP (Mexico agricultural statistics).
"""

from typing import TypedDict


# Baseline yields (kg/ha) for Jalisco region — SIAP averages for rain-fed small farms
CROP_BASELINE_YIELD: dict[str, float] = {
    "maiz": 5500.0,       # 5.5 ton/ha — Jalisco average for temporal maiz
    "frijol": 900.0,      # 0.9 ton/ha — rain-fed average
    "calabaza": 12000.0,  # 12 ton/ha — fruit weight
    "chile": 8000.0,      # 8 ton/ha — dried chile lower, fresh higher
    "jitomate": 25000.0,  # 25 ton/ha — irrigated greenhouse much higher
    "aguacate": 10000.0,  # 10 ton/ha — mature orchard average
    "agave": 40000.0,     # 40 ton/ha — 7-year harvest cycle, annualized
    "sorgo": 4500.0,      # 4.5 ton/ha — grain sorghum
    "garbanzo": 1800.0,   # 1.8 ton/ha — winter cycle
    "cana de azucar": 80000.0,  # 80 ton/ha — fresh cane
    "nopal": 50000.0,     # 50 ton/ha — intensive production
}

DEFAULT_BASELINE = 5000.0

# Uncertainty band: ±percentage around point estimate
UNCERTAINTY_BAND = 0.20  # ±20%


class YieldResult(TypedDict):
    crop_type: str
    hectares: float
    kg_per_ha: float
    min_kg_per_ha: float
    max_kg_per_ha: float
    total_kg: float
    nota: str


def predict_yield(
    crop_type: str,
    hectares: float,
    health_score: float,
) -> YieldResult:
    """Predict yield based on crop type, field area, and health score.

    Health score (0-100) scales the baseline yield:
    - 100 = full potential yield
    - 50 = 50% of potential (linear scaling with floor)
    - 0 = 20% of potential (minimum — even stressed crops produce something)

    Args:
        crop_type: Crop being grown (maiz, frijol, etc.)
        hectares: Field size
        health_score: 0-100 composite health score

    Returns:
        YieldResult with point estimate, min/max range, and total.
    """
    baseline = CROP_BASELINE_YIELD.get(crop_type or "", DEFAULT_BASELINE)

    # Health multiplier: linear scale from 0.20 (score=0) to 1.0 (score=100)
    # Floor at 0.20 — even very stressed fields produce some yield
    clamped_score = max(0.0, min(100.0, health_score))
    health_multiplier = 0.20 + (clamped_score / 100.0) * 0.80

    kg_per_ha = round(baseline * health_multiplier, 1)
    min_kg_per_ha = round(kg_per_ha * (1 - UNCERTAINTY_BAND), 1)
    max_kg_per_ha = round(kg_per_ha * (1 + UNCERTAINTY_BAND), 1)
    total_kg = round(kg_per_ha * hectares, 1)

    # Generate note in Spanish
    if health_score >= 80:
        nota = f"Rendimiento esperado bueno para {crop_type or 'cultivo'}. Campo en buen estado."
    elif health_score >= 50:
        nota = (
            f"Rendimiento moderado para {crop_type or 'cultivo'}. "
            f"Mejorar salud del campo puede incrementar produccion."
        )
    else:
        nota = (
            f"Rendimiento reducido por estres del campo. "
            f"Se recomienda atencion urgente para {crop_type or 'cultivo'}."
        )

    return YieldResult(
        crop_type=crop_type or "desconocido",
        hectares=hectares,
        kg_per_ha=kg_per_ha,
        min_kg_per_ha=min_kg_per_ha,
        max_kg_per_ha=max_kg_per_ha,
        total_kg=total_kg,
        nota=nota,
    )
