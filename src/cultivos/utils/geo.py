"""GPS coordinate utilities — polygon area calculation."""

import math


def calculate_polygon_area_hectares(coordinates: list[list[float]]) -> float:
    """Calculate area of a GPS polygon in hectares using the Shoelace formula
    with longitude/latitude to meters conversion.

    Args:
        coordinates: List of [longitude, latitude] pairs (GeoJSON order).
                     Minimum 3 points required.

    Returns:
        Area in hectares.
    """
    n = len(coordinates)
    if n < 3:
        raise ValueError("Polygon must have at least 3 coordinate pairs")

    # Convert to radians and use spherical excess approximation
    # For small polygons, project to local flat coordinates (meters) then Shoelace
    # Reference latitude = centroid for local projection
    avg_lat = sum(c[1] for c in coordinates) / n
    lat_rad = math.radians(avg_lat)

    # Meters per degree at this latitude
    meters_per_deg_lat = 111_320.0  # approximately constant
    meters_per_deg_lon = 111_320.0 * math.cos(lat_rad)

    # Convert coordinates to meters (local flat projection)
    ref_lon = coordinates[0][0]
    ref_lat = coordinates[0][1]

    xs = [(c[0] - ref_lon) * meters_per_deg_lon for c in coordinates]
    ys = [(c[1] - ref_lat) * meters_per_deg_lat for c in coordinates]

    # Shoelace formula
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += xs[i] * ys[j]
        area -= xs[j] * ys[i]
    area = abs(area) / 2.0

    # Convert m² to hectares (1 ha = 10,000 m²)
    return round(area / 10_000.0, 2)
