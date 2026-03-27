"""Drone mission planning — generate flight paths from field boundary polygons.

Pure function: coordinates in, mission plan out. No I/O, no side effects.
"""

import math
from typing import TypedDict

from cultivos.utils.geo import calculate_polygon_area_hectares


class MissionPlan(TypedDict):
    waypoints: list[list[float]]       # [[lon, lat], ...]
    pattern: str                       # "boustrophedon"
    overlap_pct: int                   # 70
    line_spacing_m: float              # meters between flight lines
    altitude_m: float                  # flight altitude in meters
    speed_ms: float                    # cruise speed m/s
    estimated_duration_min: float      # total flight time
    total_distance_m: float            # total path distance
    estimated_photos: int              # approximate photo count
    batteries_needed: int              # based on 40 min per battery
    area_hectares: float               # field area
    drone_type: str
    mission_type: str


# ── Drone specs ────────────────────────────────────────────────────────

_DRONE_SPECS = {
    "mavic_multispectral": {
        "altitude_m": 100,       # optimal for NDVI (80-120m range)
        "speed_ms": 8.0,         # ~29 km/h cruise
        "swath_m": 150,          # ground coverage width at 100m altitude
        "photo_interval_s": 2.0, # seconds between photos
        "battery_min": 40,       # minutes per battery
    },
    "mavic_thermal": {
        "altitude_m": 80,        # lower for thermal resolution (60-100m)
        "speed_ms": 7.0,
        "swath_m": 100,
        "photo_interval_s": 2.0,
        "battery_min": 40,
    },
    "agras_t100": {
        "altitude_m": 3,         # spray altitude (2-5m)
        "speed_ms": 5.0,
        "swath_m": 10,           # spray nozzle width
        "photo_interval_s": 0,   # no photos for spraying
        "battery_min": 15,       # heavier payload = shorter flight
    },
}

# ── Mission type altitude overrides ────────────────────────────────────

_MISSION_ALTITUDES = {
    "health_scan": None,        # use drone default
    "thermal_check": None,
    "spray": None,
    "emergency_recon": 60,      # lower for detail
}


def generate_mission_plan(
    boundary_coordinates: list[list[float]],
    mission_type: str = "health_scan",
    drone_type: str = "mavic_multispectral",
    overlap_pct: int = 70,
) -> MissionPlan:
    """Generate a boustrophedon flight plan from field boundary polygon.

    Args:
        boundary_coordinates: [[lon, lat], ...] polygon vertices (min 3).
        mission_type: health_scan, thermal_check, spray, emergency_recon.
        drone_type: mavic_multispectral, mavic_thermal, agras_t100.
        overlap_pct: Adjacent line overlap percentage (default 70%).

    Returns:
        MissionPlan with waypoints, timing, and resource estimates.
    """
    specs = _DRONE_SPECS.get(drone_type, _DRONE_SPECS["mavic_multispectral"])

    altitude = _MISSION_ALTITUDES.get(mission_type) or specs["altitude_m"]
    speed = specs["speed_ms"]
    swath = specs["swath_m"]
    battery_min = specs["battery_min"]
    photo_interval = specs["photo_interval_s"]

    # Line spacing = swath * (1 - overlap/100)
    line_spacing_m = swath * (1.0 - overlap_pct / 100.0)

    # Field bounding box
    lons = [c[0] for c in boundary_coordinates]
    lats = [c[1] for c in boundary_coordinates]
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)

    # Convert bounding box to meters for spacing calculation
    avg_lat = (min_lat + max_lat) / 2.0
    lat_rad = math.radians(avg_lat)
    m_per_deg_lon = 111_320.0 * math.cos(lat_rad)
    m_per_deg_lat = 111_320.0

    field_width_m = (max_lon - min_lon) * m_per_deg_lon
    field_height_m = (max_lat - min_lat) * m_per_deg_lat

    # Fly lines along the longer axis for fewer turns
    # If width >= height, fly east-west lines (vary latitude)
    # If height > width, fly north-south lines (vary longitude)
    fly_east_west = field_width_m >= field_height_m

    if fly_east_west:
        # Lines spaced in latitude, flying along longitude
        spacing_deg = line_spacing_m / m_per_deg_lat
        waypoints = _generate_boustrophedon_ew(
            min_lon, max_lon, min_lat, max_lat, spacing_deg,
        )
    else:
        # Lines spaced in longitude, flying along latitude
        spacing_deg = line_spacing_m / m_per_deg_lon
        waypoints = _generate_boustrophedon_ns(
            min_lon, max_lon, min_lat, max_lat, spacing_deg,
        )

    # Calculate total distance
    total_distance_m = _total_path_distance(waypoints, m_per_deg_lon, m_per_deg_lat)

    # Timing
    flight_time_s = total_distance_m / speed if speed > 0 else 0
    estimated_duration_min = round(flight_time_s / 60.0, 1)

    # Photos
    estimated_photos = 0
    if photo_interval > 0:
        estimated_photos = max(1, int(flight_time_s / photo_interval))

    # Batteries
    batteries_needed = max(1, math.ceil(estimated_duration_min / battery_min))

    # Area
    area = calculate_polygon_area_hectares(boundary_coordinates)

    return MissionPlan(
        waypoints=waypoints,
        pattern="boustrophedon",
        overlap_pct=overlap_pct,
        line_spacing_m=round(line_spacing_m, 1),
        altitude_m=altitude,
        speed_ms=speed,
        estimated_duration_min=estimated_duration_min,
        total_distance_m=round(total_distance_m, 1),
        estimated_photos=estimated_photos,
        batteries_needed=batteries_needed,
        area_hectares=area,
        drone_type=drone_type,
        mission_type=mission_type,
    )


def _generate_boustrophedon_ew(
    min_lon: float, max_lon: float,
    min_lat: float, max_lat: float,
    spacing_deg: float,
) -> list[list[float]]:
    """East-west boustrophedon: lines along longitude, spaced by latitude."""
    waypoints: list[list[float]] = []
    lat = min_lat
    direction = 1  # 1 = west→east, -1 = east→west
    while lat <= max_lat:
        if direction == 1:
            waypoints.append([round(min_lon, 6), round(lat, 6)])
            waypoints.append([round(max_lon, 6), round(lat, 6)])
        else:
            waypoints.append([round(max_lon, 6), round(lat, 6)])
            waypoints.append([round(min_lon, 6), round(lat, 6)])
        direction *= -1
        lat += spacing_deg
    return waypoints


def _generate_boustrophedon_ns(
    min_lon: float, max_lon: float,
    min_lat: float, max_lat: float,
    spacing_deg: float,
) -> list[list[float]]:
    """North-south boustrophedon: lines along latitude, spaced by longitude."""
    waypoints: list[list[float]] = []
    lon = min_lon
    direction = 1  # 1 = south→north, -1 = north→south
    while lon <= max_lon:
        if direction == 1:
            waypoints.append([round(lon, 6), round(min_lat, 6)])
            waypoints.append([round(lon, 6), round(max_lat, 6)])
        else:
            waypoints.append([round(lon, 6), round(max_lat, 6)])
            waypoints.append([round(lon, 6), round(min_lat, 6)])
        direction *= -1
        lon += spacing_deg
    return waypoints


def _total_path_distance(
    waypoints: list[list[float]],
    m_per_deg_lon: float,
    m_per_deg_lat: float,
) -> float:
    """Calculate total path distance in meters between sequential waypoints."""
    total = 0.0
    for i in range(len(waypoints) - 1):
        dx = (waypoints[i + 1][0] - waypoints[i][0]) * m_per_deg_lon
        dy = (waypoints[i + 1][1] - waypoints[i][1]) * m_per_deg_lat
        total += math.sqrt(dx * dx + dy * dy)
    return total
