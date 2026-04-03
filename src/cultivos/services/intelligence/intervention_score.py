"""Pure predictive intervention scoring — ranks treatments by expected impact.

No HTTP, no DB, no side effects. Takes treatment data + feedback summaries,
returns scored and ranked treatments with expected health delta, success
probability, and cost efficiency.
"""

from typing import TypedDict


class FeedbackSummary(TypedDict):
    avg_rating: float       # 1-5 average
    positive_ratio: float   # 0-1, fraction that "worked"
    count: int              # number of feedback entries


class ScoredTreatment(TypedDict):
    problema: str
    tratamiento: str
    costo_estimado_mxn: int
    urgencia: str
    health_score_used: float
    expected_health_delta: float
    success_probability: float
    cost_per_hectare: float
    intervention_score: float
    expected_roi: float
    payback_days: int
    metodo_ancestral: str | None
    scientific_basis: str | None


_URGENCY_DELTA: dict[str, float] = {
    "alta": 20.0,
    "media": 12.0,
    "baja": 5.0,
}

_DEFAULT_SUCCESS_PROB = 0.5
_ANCESTRAL_BOOST = 1.25  # 25% score boost for ancestral-method-linked treatments
# Economic conversion: MXN revenue per health point per hectare improvement
# Based on Jalisco crop yields (~$40K MXN/ha avg), 1 health point ≈ 0.8% yield
_REVENUE_PER_HEALTH_POINT = 300.0  # MXN/ha per health point
_GROWING_SEASON_DAYS = 150  # Jalisco temporal season (Jun-Oct)


def score_treatments(
    treatments: list[dict],
    feedback: dict[str, FeedbackSummary],
    hectares: float,
) -> list[ScoredTreatment]:
    """Score and rank treatments by composite intervention score.

    Composite score = expected_health_delta * success_probability / cost_per_hectare_normalized

    - expected_health_delta: based on urgency and how low the current health is
    - success_probability: from farmer feedback if available, else 0.5 default
    - cost_per_hectare: MXN / hectares (lower is better for the farmer)
    - ancestral boost: treatments linked to ancestral methods get a 1.25x multiplier

    Returns treatments sorted by intervention_score descending.
    """
    if not treatments:
        return []

    effective_ha = max(hectares, 1.0)
    scored: list[ScoredTreatment] = []

    for t in treatments:
        problema = t.get("problema", "")
        urgencia = t.get("urgencia", "media")
        costo = t.get("costo_estimado_mxn", 0)
        health_used = t.get("health_score_used", 50.0)
        ancestral_name = t.get("ancestral_method_name") or None
        ancestral_science = t.get("ancestral_base_cientifica") or None

        # Expected health delta: based on urgency + room for improvement
        base_delta = _URGENCY_DELTA.get(urgencia, 12.0)
        room = max(100.0 - health_used, 0.0) / 100.0  # 0-1 scale
        expected_health_delta = round(base_delta * (0.5 + 0.5 * room), 1)

        # Success probability from feedback data
        fb = feedback.get(problema)
        if fb and fb["count"] > 0:
            # Weighted: 60% positive_ratio + 40% normalized rating
            success_probability = round(
                0.6 * fb["positive_ratio"] + 0.4 * (fb["avg_rating"] / 5.0), 2
            )
        else:
            success_probability = _DEFAULT_SUCCESS_PROB

        # Cost efficiency
        cost_per_hectare = round(costo / effective_ha, 1)

        # Composite score: delta * probability / normalized_cost
        # Normalize cost to 0-1 range (cap at 5000 MXN/ha)
        cost_factor = max(1.0 - cost_per_hectare / 5000.0, 0.1)
        intervention_score = round(
            expected_health_delta * success_probability * cost_factor, 2
        )

        # Ancestral method boost: indigenous wisdom synergy
        if ancestral_name:
            intervention_score = round(intervention_score * _ANCESTRAL_BOOST, 2)

        # Cost-benefit: ROI and payback period
        benefit_per_ha = expected_health_delta * success_probability * _REVENUE_PER_HEALTH_POINT
        if cost_per_hectare <= 0:
            expected_roi = 100.0
            payback_days = 0
        elif benefit_per_ha <= 0:
            expected_roi = -100.0
            payback_days = 999
        else:
            expected_roi = round(
                ((benefit_per_ha - cost_per_hectare) / cost_per_hectare) * 100, 1
            )
            daily_benefit = benefit_per_ha / _GROWING_SEASON_DAYS
            payback_days = min(int(cost_per_hectare / daily_benefit), 999)

        scored.append(ScoredTreatment(
            problema=problema,
            tratamiento=t.get("tratamiento", ""),
            costo_estimado_mxn=costo,
            urgencia=urgencia,
            health_score_used=health_used,
            expected_health_delta=expected_health_delta,
            success_probability=success_probability,
            cost_per_hectare=cost_per_hectare,
            intervention_score=intervention_score,
            expected_roi=expected_roi,
            payback_days=payback_days,
            metodo_ancestral=ancestral_name,
            scientific_basis=ancestral_science,
        ))

    scored.sort(key=lambda x: x["intervention_score"], reverse=True)
    return scored
