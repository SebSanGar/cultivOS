"""Pure crop photo analysis — image bytes in, analysis dict out.

No I/O, no database, no HTTP. Just image processing.
"""

from __future__ import annotations

import io
from collections import Counter

from PIL import Image


def analyze_crop_photo(image_bytes: bytes) -> dict:
    """Analyze a crop photo and return color histogram + classification.

    Args:
        image_bytes: Raw image file bytes (JPEG/PNG).

    Returns:
        dict with dominant_colors, avg_brightness, green_ratio, classification.

    Raises:
        ValueError: If image_bytes cannot be decoded as an image.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as exc:
        raise ValueError(f"Cannot decode image: {exc}") from exc

    # Resize for speed (max 200px wide)
    if img.width > 200:
        ratio = 200 / img.width
        img = img.resize((200, int(img.height * ratio)))

    pixels = list(img.getdata())
    total = len(pixels)

    # Quantize colors to 8-level buckets for dominant color detection
    def _bucket(val: int) -> int:
        return (val // 32) * 32

    bucketed = [(_bucket(r), _bucket(g), _bucket(b)) for r, g, b in pixels]
    counts = Counter(bucketed).most_common(5)
    dominant_colors = [
        {"color": list(color), "percentage": round(cnt / total * 100, 1)}
        for color, cnt in counts
    ]

    # Average brightness (0-255)
    avg_brightness = round(sum(sum(p) / 3 for p in pixels) / total, 1)

    # Green ratio: proportion of pixels where G > R and G > B
    green_pixels = sum(1 for r, g, b in pixels if g > r and g > b)
    green_ratio = round(green_pixels / total, 3)

    # Basic classification
    classification = _classify(green_ratio, avg_brightness)

    return {
        "dominant_colors": dominant_colors,
        "avg_brightness": avg_brightness,
        "green_ratio": green_ratio,
        "classification": classification,
    }


def _classify(green_ratio: float, avg_brightness: float) -> str:
    """Classify image based on green ratio and brightness."""
    if green_ratio >= 0.4:
        return "healthy_vegetation"
    elif green_ratio >= 0.2:
        return "stressed_vegetation"
    elif avg_brightness > 160:
        return "bare_soil"
    else:
        return "mixed"
