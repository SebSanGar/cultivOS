"""Pydantic schemas for cooperative weekly agenda."""

from pydantic import BaseModel


class AgendaItemOut(BaseModel):
    farm_name: str
    field_name: str
    priority_score: float
    top_issue: str
    accion_es: str


class AgendaSemanalOut(BaseModel):
    coop_name: str
    total_farms: int
    total_fields: int
    top_items: list[AgendaItemOut]
    resumen_es: str
