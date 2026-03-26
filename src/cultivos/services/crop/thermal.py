"""Pure thermal stress computation — arrays in, results out. No HTTP, no S3, no side effects."""

from typing import TypedDict

import numpy as np

STRESS_THRESHOLD_C = 35.0  # pixels above this are heat-stressed
IRRIGATION_DEFICIT_VARIATION_C = 5.0  # max-min above this flags irrigation deficit


class ThermalStats(TypedDict):
    temp_mean: float
    temp_std: float
    temp_min: float
    temp_max: float
    pixels_total: int
    stress_pct: float  # % of pixels above STRESS_THRESHOLD_C
    irrigation_deficit: bool  # True if temp variation > IRRIGATION_DEFICIT_VARIATION_C


def compute_thermal_stress(thermal: np.ndarray) -> ThermalStats:
    """Compute thermal stress statistics from a temperature array (Celsius).

    Pixels with temperature > 35 C are classified as heat-stressed.
    If max - min > 5 C, irrigation_deficit is flagged.
    """
    total = int(thermal.size)
    if total == 0:
        return ThermalStats(
            temp_mean=0.0,
            temp_std=0.0,
            temp_min=0.0,
            temp_max=0.0,
            pixels_total=0,
            stress_pct=0.0,
            irrigation_deficit=False,
        )

    temp_min = float(np.min(thermal))
    temp_max = float(np.max(thermal))
    stressed_pixels = int(np.sum(thermal > STRESS_THRESHOLD_C))
    variation = temp_max - temp_min

    return ThermalStats(
        temp_mean=round(float(np.mean(thermal)), 2),
        temp_std=round(float(np.std(thermal)), 2),
        temp_min=round(temp_min, 2),
        temp_max=round(temp_max, 2),
        pixels_total=total,
        stress_pct=round(stressed_pixels / total * 100, 1),
        irrigation_deficit=variation > IRRIGATION_DEFICIT_VARIATION_C,
    )
