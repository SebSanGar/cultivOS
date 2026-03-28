"""Pydantic schemas for the comprehensive field intelligence endpoint."""

from datetime import datetime

from pydantic import BaseModel


class IntelNDVI(BaseModel):
    ndvi_mean: float
    ndvi_std: float
    stress_pct: float
    zones: list[dict] | None = None
    analyzed_at: datetime

    model_config = {"from_attributes": True}


class IntelThermal(BaseModel):
    temp_mean: float
    temp_max: float
    temp_min: float
    stress_pct: float
    irrigation_deficit: bool
    analyzed_at: datetime

    model_config = {"from_attributes": True}


class IntelSoil(BaseModel):
    ph: float | None
    organic_matter_pct: float | None
    nitrogen_ppm: float | None
    phosphorus_ppm: float | None
    potassium_ppm: float | None
    texture: str | None
    moisture_pct: float | None
    sampled_at: datetime

    model_config = {"from_attributes": True}


class IntelMicrobiome(BaseModel):
    respiration_rate: float
    microbial_biomass_carbon: float
    fungi_bacteria_ratio: float
    classification: str
    sampled_at: datetime

    model_config = {"from_attributes": True}


class IntelHealth(BaseModel):
    score: float
    trend: str
    sources: list[str]
    breakdown: dict[str, float]
    scored_at: datetime

    model_config = {"from_attributes": True}


class IntelWeather(BaseModel):
    temp_c: float
    humidity_pct: float
    wind_kmh: float
    rainfall_mm: float
    description: str
    forecast_3day: list[dict]
    recorded_at: datetime

    model_config = {"from_attributes": True}


class IntelGrowthStage(BaseModel):
    stage: str
    stage_es: str
    days_since_planting: int
    days_in_stage: int
    days_until_next_stage: int | None
    water_multiplier: float
    nutrient_focus: str


class IntelDiseaseRisk(BaseModel):
    risk_level: str
    mensaje: str
    risks: list[dict]


class IntelYield(BaseModel):
    kg_per_ha: float
    min_kg_per_ha: float
    max_kg_per_ha: float
    total_kg: float
    nota: str


class IntelTreatment(BaseModel):
    id: int
    problema: str
    tratamiento: str
    urgencia: str
    organic: bool
    costo_estimado_mxn: int
    created_at: datetime

    model_config = {"from_attributes": True}


class IntelCarbon(BaseModel):
    soc_pct: float | None
    soc_tonnes_per_ha: float | None
    clasificacion: str | None
    tendencia: str


class IntelFusion(BaseModel):
    confidence: float
    contradictions: list[dict]
    sensors_used: list[str]
    assessment: str


class FieldIntelligenceOut(BaseModel):
    """Comprehensive field intelligence — all Cerebro data in one response."""
    field_id: int
    field_name: str
    crop_type: str | None
    hectares: float | None
    planted_at: datetime | None

    health: IntelHealth | None = None
    ndvi: IntelNDVI | None = None
    thermal: IntelThermal | None = None
    soil: IntelSoil | None = None
    microbiome: IntelMicrobiome | None = None
    weather: IntelWeather | None = None
    growth_stage: IntelGrowthStage | None = None
    disease_risk: IntelDiseaseRisk | None = None
    yield_prediction: IntelYield | None = None
    treatments: list[IntelTreatment] = []
    carbon: IntelCarbon | None = None
    fusion: IntelFusion | None = None
