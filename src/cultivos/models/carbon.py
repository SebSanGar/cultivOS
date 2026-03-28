"""Pydantic schemas for soil carbon tracking endpoints."""

from pydantic import BaseModel


class SOCEstimateOut(BaseModel):
    organic_matter_pct: float
    soc_pct: float
    soc_tonnes_per_ha: float
    depth_cm: float
    bulk_density: float
    clasificacion: str  # bajo, adecuado, alto


class FarmCarbonFieldEntry(BaseModel):
    field_id: int
    field_name: str
    hectares: float
    soc_tonnes_per_ha: float
    co2e_tonnes: float
    clasificacion: str
    tendencia: str


class FarmCarbonSummaryOut(BaseModel):
    total_fields: int
    total_hectares: float = 0
    avg_soc_tonnes_per_ha: float = 0
    total_co2e_tonnes: float = 0
    soc_per_ha_rate: float = 0
    fields: list[FarmCarbonFieldEntry] = []


class CarbonReportOut(BaseModel):
    field_id: int
    soc_actual: SOCEstimateOut | None = None
    tendencia: str  # ganando, estable, perdiendo, datos_insuficientes
    cambio_soc_tonnes_per_ha: float
    registros: int
    recomendaciones: list[str]
    resumen: str  # Spanish-language summary
