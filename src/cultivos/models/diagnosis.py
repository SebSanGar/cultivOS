"""Pydantic schemas for crop problem diagnosis endpoint."""

from pydantic import BaseModel


class DiagnoseRequest(BaseModel):
    phrase: str
    crop: str | None = None
    field_id: int | None = None


class DiagnoseOut(BaseModel):
    matched_phrase: str | None
    formal_term_es: str | None
    likely_cause: str | None
    recommended_action: str | None
    treatments: list[dict]
