"""Pydantic models for cooperative FODECIJAL readiness score endpoint."""

from pydantic import BaseModel


class FodecijalSubScore(BaseModel):
    name: str
    score: float  # 0-100
    weight: float  # 0.0-1.0
    evidence_es: str  # Spanish explanation bullet


class FodecijalReadinessOut(BaseModel):
    cooperative_id: int
    overall_score: float  # weighted avg 0-100
    sub_scores: list[FodecijalSubScore]
    farm_count: int
    field_count: int
