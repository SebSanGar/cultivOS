"""Pydantic schemas for the Dashboard API."""

from datetime import datetime

from pydantic import BaseModel


class DashboardFarm(BaseModel):
    id: int
    name: str
    owner_name: str | None
    location_lat: float | None
    location_lon: float | None
    total_hectares: float | None
    municipality: str | None
    state: str | None
    country: str | None

    model_config = {"from_attributes": True}


class DashboardHealthScore(BaseModel):
    id: int
    score: float
    trend: str
    sources: list[str]
    breakdown: dict[str, float]
    scored_at: datetime

    model_config = {"from_attributes": True}


class DashboardNDVI(BaseModel):
    id: int
    ndvi_mean: float
    ndvi_std: float
    stress_pct: float
    analyzed_at: datetime

    model_config = {"from_attributes": True}


class DashboardSoil(BaseModel):
    id: int
    ph: float | None
    organic_matter_pct: float | None
    texture: str | None
    moisture_pct: float | None
    sampled_at: datetime

    model_config = {"from_attributes": True}


class DashboardWeather(BaseModel):
    temp_c: float
    humidity_pct: float
    wind_kmh: float
    description: str
    recorded_at: datetime

    model_config = {"from_attributes": True}


class DashboardField(BaseModel):
    id: int
    name: str
    crop_type: str | None
    hectares: float | None
    latest_health_score: DashboardHealthScore | None
    latest_ndvi: DashboardNDVI | None
    latest_soil: DashboardSoil | None


class DashboardTopRisk(BaseModel):
    field_name: str
    score: float
    trend: str


class DashboardOut(BaseModel):
    farm: DashboardFarm
    fields: list[DashboardField]
    overall_health: float | None
    weather: DashboardWeather | None
    treatment_count: int = 0
    top_risk: DashboardTopRisk | None = None
