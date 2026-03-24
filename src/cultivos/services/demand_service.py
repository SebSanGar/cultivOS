"""Demand forecasting — pure functions for par level recommendations.

No DB, no HTTP. Data in, results out.
"""

import math
from decimal import Decimal, ROUND_HALF_UP

from cultivos.models.production import ParLevelRecommendation


def calculate_safety_buffer(
    demand_stddev: Decimal,
    service_level_factor: Decimal = Decimal("1.3"),
) -> int:
    """Safety buffer = demand volatility * service level factor.

    Service level 1.3 targets ~95% fill rate.
    """
    return math.ceil(float(demand_stddev * service_level_factor))


def recommend_par(
    recipe_id: int,
    avg_demand: Decimal,
    demand_stddev: Decimal,
    service_level_factor: Decimal = Decimal("1.3"),
) -> ParLevelRecommendation:
    """Recommend par level based on demand statistics.

    Par = avg_demand + safety_buffer
    """
    base = math.ceil(float(avg_demand))
    buffer = calculate_safety_buffer(demand_stddev, service_level_factor)
    return ParLevelRecommendation(
        recipe_id=recipe_id,
        avg_demand=avg_demand,
        demand_stddev=demand_stddev,
        recommended_base_par=base,
        recommended_safety_buffer=buffer,
        recommended_effective_par=base + buffer,
    )


def simple_moving_average(values: list[int], window: int = 7) -> Decimal:
    """Calculate simple moving average from recent values."""
    if not values:
        return Decimal("0")
    recent = values[-window:]
    return Decimal(str(sum(recent) / len(recent))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def standard_deviation(values: list[int]) -> Decimal:
    """Calculate standard deviation of values."""
    if len(values) < 2:
        return Decimal("0")
    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    return Decimal(str(math.sqrt(variance))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
