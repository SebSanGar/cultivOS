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


# ── Batch health assessment ──────────────────────────────────────────


class BatchHealthRequestIn(BaseModel):
    field_ids: list[int]


class BatchHealthEntry(BaseModel):
    field_id: int
    field_name: Optional[str] = None
    farm_name: Optional[str] = None
    score: Optional[float] = None
    trend: Optional[str] = None
    sources: Optional[list[str]] = None
    breakdown: Optional[dict[str, float]] = None


class BatchHealthOut(BaseModel):
    results: list[BatchHealthEntry]


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


# ── Aggregate economics ─────────────────────────────────────────────


class FarmEconomicsEntry(BaseModel):
    farm_id: int
    farm_name: str
    hectares: float
    water_savings_mxn: int = 0
    fertilizer_savings_mxn: int = 0
    yield_improvement_mxn: int = 0
    total_savings_mxn: int = 0


class IntelEconomicsOut(BaseModel):
    total_farms: int
    total_hectares: float
    water_savings_mxn: int = 0
    fertilizer_savings_mxn: int = 0
    yield_improvement_mxn: int = 0
    total_savings_mxn: int = 0
    farms: list[FarmEconomicsEntry] = []


# ── Aggregate carbon sequestration ─────────────────────────────────


class CarbonFieldEntry(BaseModel):
    field_id: int
    field_name: str
    farm_name: str
    hectares: float
    soc_tonnes_per_ha: float
    clasificacion: str
    tendencia: str


class IntelCarbonSummaryOut(BaseModel):
    total_fields: int
    total_hectares: float = 0
    avg_soc_tonnes_per_ha: float = 0
    total_sequestration_tonnes: float = 0  # CO2e = SOC * 3.67 * hectares
    fields: list[CarbonFieldEntry] = []


# ── Sensor fusion overview ────────────────────────────────────────────


class FusionContradictionEntry(BaseModel):
    tag: str
    sensors: list[str]
    description: str


class FusionFieldEntry(BaseModel):
    field_id: int
    field_name: str
    farm_name: str
    confidence: float
    sensors_used: list[str]
    contradictions: list[FusionContradictionEntry]
    assessment: str


class SensorFusionOverviewOut(BaseModel):
    total_fields: int
    fields_with_data: int
    avg_confidence: float = 0
    total_contradictions: int = 0
    fields: list[FusionFieldEntry] = []
