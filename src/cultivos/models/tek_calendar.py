"""Pydantic schema for TEK practice seasonal calendar endpoint."""

from typing import List, Optional
from pydantic import BaseModel


class TEKCalendarEntryOut(BaseModel):
    method_name: str
    description_es: str
    timing_rationale: Optional[str] = None
    crop_types: List[str]
    ecological_benefit: Optional[int] = None
