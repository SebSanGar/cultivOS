"""Pydantic schemas for agronomist tips knowledge base."""

from pydantic import BaseModel


class AgronomistTipOut(BaseModel):
    id: int
    crop: str
    problem: str
    tip_text_es: str
    source: str | None = None
    region: str | None = None
    season: str | None = None

    model_config = {"from_attributes": True}
