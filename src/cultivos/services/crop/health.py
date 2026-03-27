"""Pure health scoring — data in, score out. No HTTP, no DB, no side effects.

Combines NDVI stats and soil analysis into a 0-100 field health score.
Handles partial inputs via proportional weight redistribution.
"""

from typing import TypedDict


class SoilInput(TypedDict, total=False):
    ph: float | None
    organic_matter_pct: float | None
    nitrogen_ppm: float | None
    phosphorus_ppm: float | None
    potassium_ppm: float | None
    moisture_pct: float | None


class NDVIInput(TypedDict, total=False):
    ndvi_mean: float
    ndvi_std: float
    stress_pct: float


class MicrobiomeInput(TypedDict, total=False):
    respiration_rate: float
    microbial_biomass_carbon: float
    fungi_bacteria_ratio: float
    classification: str  # healthy, moderate, degraded


class HealthResult(TypedDict):
    score: int  # 0-100
    trend: str  # improving, stable, declining
    sources: list[str]
    breakdown: dict[str, float]  # component name → sub-score


# --- Base weights (sum to 1.0) ---
_BASE_WEIGHTS = {
    "ndvi": 0.45,
    "soil": 0.20,
    "microbiome": 0.15,
    "trend": 0.20,
}


def _score_ndvi(ndvi: NDVIInput) -> float:
    """Score NDVI component 0-100.

    ndvi_mean drives the base score (0-1 mapped to 0-100).
    Uniformity bonus: low std relative to mean improves score.
    Stress penalty: high stress_pct reduces score.
    """
    mean = ndvi.get("ndvi_mean", 0.0)
    std = ndvi.get("ndvi_std", 0.0)
    stress = ndvi.get("stress_pct", 0.0)

    # Base: ndvi_mean mapped to 0-100 (clamped)
    base = max(0.0, min(mean, 1.0)) * 100

    # Uniformity bonus: low std → up to +10 (std < 0.05 is very uniform)
    uniformity_bonus = max(0.0, 10 * (1 - min(std / 0.15, 1.0)))

    # Stress penalty: stress_pct directly penalizes
    stress_penalty = stress * 0.3

    return max(0.0, min(100.0, base + uniformity_bonus - stress_penalty))


def _score_soil(soil: SoilInput) -> float:
    """Score soil health 0-100 from available soil metrics.

    pH: optimal 6.0-7.0 → 100, drops off outside.
    organic_matter_pct: >5% excellent, 3-5% good, <2% poor.
    NPK: each scored on presence and reasonable range.
    moisture_pct: 20-60% optimal.
    """
    sub_scores: list[float] = []

    ph = soil.get("ph")
    if ph is not None:
        # Optimal: 6.0-7.0 → 100. Each 0.5 outside → -15
        if 6.0 <= ph <= 7.0:
            sub_scores.append(100.0)
        else:
            distance = max(0.0, min(abs(ph - 6.5) - 0.5, 3.5))
            sub_scores.append(max(0.0, 100 - distance * 30))

    om = soil.get("organic_matter_pct")
    if om is not None:
        # >5% → 100, 3-5 → 70-100, 1-3 → 30-70, <1 → 0-30
        if om >= 5:
            sub_scores.append(100.0)
        elif om >= 3:
            sub_scores.append(70 + (om - 3) * 15)
        elif om >= 1:
            sub_scores.append(30 + (om - 1) * 20)
        else:
            sub_scores.append(om * 30)

    n = soil.get("nitrogen_ppm")
    if n is not None:
        # 20-60 ppm optimal for most crops
        if 20 <= n <= 60:
            sub_scores.append(100.0)
        elif n < 20:
            sub_scores.append(max(0.0, n / 20 * 80))
        else:
            sub_scores.append(max(40.0, 100 - (n - 60) * 0.5))

    p = soil.get("phosphorus_ppm")
    if p is not None:
        # 15-40 ppm optimal
        if 15 <= p <= 40:
            sub_scores.append(100.0)
        elif p < 15:
            sub_scores.append(max(0.0, p / 15 * 80))
        else:
            sub_scores.append(max(40.0, 100 - (p - 40) * 0.5))

    k = soil.get("potassium_ppm")
    if k is not None:
        # 100-250 ppm optimal
        if 100 <= k <= 250:
            sub_scores.append(100.0)
        elif k < 100:
            sub_scores.append(max(0.0, k / 100 * 80))
        else:
            sub_scores.append(max(40.0, 100 - (k - 250) * 0.2))

    moisture = soil.get("moisture_pct")
    if moisture is not None:
        # 20-60% optimal
        if 20 <= moisture <= 60:
            sub_scores.append(100.0)
        elif moisture < 20:
            sub_scores.append(max(0.0, moisture / 20 * 80))
        else:
            sub_scores.append(max(0.0, 100 - (moisture - 60) * 2.5))

    if not sub_scores:
        return 50.0  # no soil data → neutral score

    return sum(sub_scores) / len(sub_scores)


def _score_microbiome(micro: MicrobiomeInput) -> float:
    """Score microbiome health 0-100.

    Classification drives base score: healthy=90, moderate=60, degraded=25.
    Fungi:bacteria ratio bonus: >1.0 adds up to +10 (indicates mature soil ecosystem).
    Biomass carbon bonus: >300 mg C/kg adds up to +5.
    """
    classification = micro.get("classification", "moderate")
    base = {"healthy": 90.0, "moderate": 60.0, "degraded": 25.0}.get(classification, 60.0)

    fbr = micro.get("fungi_bacteria_ratio", 0.5)
    fbr_bonus = min(10.0, max(0.0, (fbr - 0.5) * 10))

    mbc = micro.get("microbial_biomass_carbon", 0.0)
    mbc_bonus = min(5.0, max(0.0, (mbc - 200) / 100 * 5))

    return max(0.0, min(100.0, base + fbr_bonus + mbc_bonus))


def _compute_trend(current_score: float, previous_score: float | None) -> str:
    """Determine trend from current vs previous score."""
    if previous_score is None:
        return "stable"  # no history → neutral
    diff = current_score - previous_score
    if diff > 5:
        return "improving"
    elif diff < -5:
        return "declining"
    return "stable"


def _score_trend(trend: str) -> float:
    """Score the trend component 0-100."""
    return {"improving": 90.0, "stable": 60.0, "declining": 20.0}.get(trend, 60.0)


def compute_health_score(
    ndvi: NDVIInput | None = None,
    soil: SoilInput | None = None,
    previous_score: float | None = None,
    microbiome: MicrobiomeInput | None = None,
) -> HealthResult:
    """Compute composite health score 0-100 from available inputs.

    Weights are redistributed proportionally when inputs are missing.
    Always returns a score — partial data is better than no data.
    """
    available: dict[str, float] = {}
    sources: list[str] = []
    breakdown: dict[str, float] = {}

    if ndvi is not None:
        ndvi_score = _score_ndvi(ndvi)
        available["ndvi"] = ndvi_score
        breakdown["ndvi"] = round(ndvi_score, 1)
        sources.append("ndvi")

    if soil is not None:
        soil_score = _score_soil(soil)
        available["soil"] = soil_score
        breakdown["soil"] = round(soil_score, 1)
        sources.append("soil")

    if microbiome is not None:
        micro_score = _score_microbiome(microbiome)
        available["microbiome"] = micro_score
        breakdown["microbiome"] = round(micro_score, 1)
        sources.append("microbiome")

    # Trend is always computed (stable if no history)
    # But we need at least one primary input to have a meaningful score
    if not available:
        return HealthResult(
            score=0,
            trend="stable",
            sources=[],
            breakdown={},
        )

    # Compute raw score from primary inputs first (to determine trend)
    primary_weights = {k: _BASE_WEIGHTS[k] for k in available}
    total_primary_weight = sum(primary_weights.values())
    normalized_primary = {k: v / total_primary_weight for k, v in primary_weights.items()}

    raw_score = sum(available[k] * normalized_primary[k] for k in available)

    # Trend
    trend = _compute_trend(raw_score, previous_score)
    trend_score = _score_trend(trend)
    breakdown["trend"] = round(trend_score, 1)

    # Final score: redistribute all weights including trend
    available["trend"] = trend_score
    all_weights = {k: _BASE_WEIGHTS[k] for k in available}
    total_weight = sum(all_weights.values())
    normalized = {k: v / total_weight for k, v in all_weights.items()}

    final = sum(available[k] * normalized[k] for k in available)
    score = max(0, min(100, round(final)))

    return HealthResult(
        score=score,
        trend=trend,
        sources=sources,
        breakdown=breakdown,
    )
