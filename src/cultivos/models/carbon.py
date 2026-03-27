"""Pydantic schemas for soil carbon tracking endpoints."""

from pydantic import BaseModel


class SOCEstimateOut(BaseModel):
    organic_matter_pct: float
    soc_pct: float
    soc_tonnes_per_ha: float
    depth_cm: float
    bulk_density: float
    clasificacion: str  # bajo, adecuado, alto


class CarbonReportOut(BaseModel):
    field_id: int
    soc_actual: SOCEstimateOut | None = None
    tendencia: str  # ganando, estable, perdiendo, datos_insuficientes
    cambio_soc_tonnes_per_ha: float
    registros: int
    recomendaciones: list[str]
    resumen: str  # Spanish-language summary
