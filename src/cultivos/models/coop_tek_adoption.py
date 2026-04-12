"""Pydantic schemas for cooperative TEK practice adoption rate endpoint."""

from pydantic import BaseModel


class CoopTekFarmEntry(BaseModel):
    farm_id: int
    farm_name: str
    avg_alignment_pct: float
    fields_assessed: int


class CoopTekAdoptionOut(BaseModel):
    cooperative_id: int
    month: int
    overall_adoption_pct: float
    top_practice_es: str | None
    total_fields_assessed: int
    farms: list[CoopTekFarmEntry]
