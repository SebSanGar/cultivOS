"""Pydantic schemas for drone mission planning."""

from pydantic import BaseModel


class MissionPlanOut(BaseModel):
    waypoints: list[list[float]]
    pattern: str
    overlap_pct: int
    line_spacing_m: float
    altitude_m: float
    speed_ms: float
    estimated_duration_min: float
    total_distance_m: float
    estimated_photos: int
    batteries_needed: int
    area_hectares: float
    drone_type: str
    mission_type: str
