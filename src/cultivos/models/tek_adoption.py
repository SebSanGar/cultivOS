"""Pydantic models for #207 farm ancestral method adoption log."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class TEKAdoptionIn(BaseModel):
    method_name: str
    adopted_at: datetime
    fields_applied: List[int]
    farmer_notes_es: Optional[str] = ""


class TEKAdoptionOut(BaseModel):
    id: int
    method_name: str
    adopted_at: datetime
    fields_count: int
    farmer_notes_es: Optional[str] = ""
    ecological_benefit: Optional[int] = None

    model_config = {"from_attributes": True}


class TEKAdoptionListOut(BaseModel):
    farm_id: int
    adoptions: List[TEKAdoptionOut]
    adoption_count: int
    most_recent_adoption_at: Optional[datetime] = None
