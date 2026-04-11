"""Pydantic models for active alert summary endpoint."""

from pydantic import BaseModel


class ActiveAlertsSummaryOut(BaseModel):
    farm_id: int
    critical_count: int
    high_count: int
    top_action_es: str
    next_check_date: str  # ISO date
    safe: bool
