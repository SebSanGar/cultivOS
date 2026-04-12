"""Pydantic model for cooperative FODECIJAL evidence pack (task #208)."""

from datetime import datetime

from pydantic import BaseModel


class CoopEvidencePackOut(BaseModel):
    cooperative_id: int
    cooperative_name: str
    readiness_score: float
    portfolio_health_avg: float | None
    total_co2e_sequestered_t: float
    outbreak_risk_level: str
    regen_adoption_pct: float
    shannon_diversity_index: float
    top_strength_es: str
    top_weakness_es: str
    generated_at: datetime
