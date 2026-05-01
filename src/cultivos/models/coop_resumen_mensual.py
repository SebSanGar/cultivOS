"""Pydantic schemas for cooperative monthly summary."""

from typing import Optional

from pydantic import BaseModel


class ResumenMensualOut(BaseModel):
    coop_name: str
    total_farms: int
    total_fields: int
    period_days: int
    avg_health_change: Optional[float]
    total_treatments: int
    total_alerts: int
    resumen_es: str
