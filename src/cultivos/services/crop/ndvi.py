"""Pure NDVI computation — arrays in, results out. No HTTP, no S3, no side effects."""

from typing import TypedDict

import numpy as np


class NDVIZoneCount(TypedDict):
    classification: str
    min_ndvi: float
    max_ndvi: float
    pixel_count: int
    percentage: float


class NDVIStats(TypedDict):
    ndvi_mean: float
    ndvi_std: float
    ndvi_min: float
    ndvi_max: float
    pixels_total: int
    stress_pct: float  # % of pixels below 0.4 (severe stress + critical)
    zones: list[NDVIZoneCount]


NDVI_ZONES = [
    ("critical", 0.0, 0.2),
    ("severe_stress", 0.2, 0.4),
    ("moderate_stress", 0.4, 0.6),
    ("healthy", 0.6, 0.8),
    ("excellent", 0.8, 1.0),
]


def compute_ndvi(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
    """Compute NDVI from NIR and Red band arrays.

    Formula: (NIR - Red) / (NIR + Red)
    Returns values clamped to [-1, 1]. Division-by-zero pixels → 0.
    """
    nir = nir.astype(np.float64)
    red = red.astype(np.float64)
    denominator = nir + red
    with np.errstate(divide="ignore", invalid="ignore"):
        ndvi = np.where(denominator == 0, 0.0, (nir - red) / denominator)
    return np.clip(ndvi, -1.0, 1.0)


def compute_ndvi_stats(ndvi: np.ndarray) -> NDVIStats:
    """Compute summary statistics and zone classification from an NDVI array.

    Only considers pixels >= 0 (ignores water/shadow with negative NDVI).
    """
    valid = ndvi[ndvi >= 0]
    total = int(valid.size)

    if total == 0:
        return NDVIStats(
            ndvi_mean=0.0,
            ndvi_std=0.0,
            ndvi_min=0.0,
            ndvi_max=0.0,
            pixels_total=0,
            stress_pct=0.0,
            zones=[],
        )

    stress_pixels = int(np.sum(valid < 0.4))

    zones: list[NDVIZoneCount] = []
    for classification, lo, hi in NDVI_ZONES:
        count = int(np.sum((valid >= lo) & (valid < hi)))
        zones.append(NDVIZoneCount(
            classification=classification,
            min_ndvi=lo,
            max_ndvi=hi,
            pixel_count=count,
            percentage=round(count / total * 100, 1),
        ))

    return NDVIStats(
        ndvi_mean=round(float(np.mean(valid)), 4),
        ndvi_std=round(float(np.std(valid)), 4),
        ndvi_min=round(float(np.min(valid)), 4),
        ndvi_max=round(float(np.max(valid)), 4),
        pixels_total=total,
        stress_pct=round(stress_pixels / total * 100, 1),
        zones=zones,
    )
