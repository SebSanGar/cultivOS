"""Pydantic models for intelligence dashboard API."""

from pydantic import BaseModel
from typing import Optional


class WorstField(BaseModel):
    field_id: int
    field_name: str
    farm_name: str
    score: float


class IntelSummaryOut(BaseModel):
    total_farms: int
    total_fields: int
    avg_health: Optional[float] = None
    worst_field: Optional[WorstField] = None


class SoilTrendEntry(BaseModel):
    date: str
    avg_ph: float
    avg_organic_matter: float
    sample_count: int


class SoilTrendsOut(BaseModel):
    trends: list[SoilTrendEntry]


class TreatmentEffectivenessEntry(BaseModel):
    field_name: str
    farm_name: str
    tratamiento: str
    health_before: float
    health_after: Optional[float] = None
    delta: Optional[float] = None
    urgencia: str
    organic: bool


class TreatmentEffectivenessOut(BaseModel):
    treatments: list[TreatmentEffectivenessEntry]


class AnomalyEntry(BaseModel):
    field_id: int
    field_name: str
    farm_name: str
    consecutive_declines: int
    latest_score: float
    score_history: list[float]


class AnomaliesOut(BaseModel):
    anomalies: list[AnomalyEntry]


class SeasonEntry(BaseModel):
    season: str  # "temporal" or "secas"
    year: int  # start year of the season
    avg_score: float
    count: int
    status: str  # "ok" or "insufficient_data"


class SeasonalOut(BaseModel):
    seasons: list[SeasonEntry]


# ── Treatment timing optimizer ─────────────────────────────────────────


class ForecastDayIn(BaseModel):
    description: str
    temp_c: float = 28.0
    humidity_pct: float = 55.0
    wind_kmh: float = 8.0


class TimingRequestIn(BaseModel):
    treatment_type: str  # organic_amendment, foliar_spray, soil_drench
    forecast_3day: list[ForecastDayIn]


class TimingOut(BaseModel):
    best_day: int
    best_time: str
    reason: str
    avoid_days: list[int]


# ── Farm comparison ───────────────────────────────────────────────────


# ── Treatment effectiveness report ───────────────────────────────────


class TreatmentEffectivenessReportEntry(BaseModel):
    tratamiento: str
    total_applications: int
    feedback_count: int
    feedback_success_rate: Optional[float] = None  # % of feedback where worked=True
    avg_rating: Optional[float] = None
    avg_health_delta: Optional[float] = None
    composite_score: float  # weighted combo of success rate + delta


class TreatmentEffectivenessReportOut(BaseModel):
    treatments: list[TreatmentEffectivenessReportEntry]


class FarmCompareEntry(BaseModel):
    farm_id: int
    farm_name: str
    field_count: int
    total_hectares: float
    avg_health: Optional[float] = None
    yield_total_kg: float = 0
    treatment_count: int = 0


class FarmCompareOut(BaseModel):
    farms: list[FarmCompareEntry]
