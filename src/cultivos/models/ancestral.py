"""Pydantic schemas for ancestral farming methods knowledge base."""

from pydantic import BaseModel


class AncestralMethodOut(BaseModel):
    id: int
    name: str
    description_es: str
    region: str
    practice_type: str
    crops: list[str]
    benefits_es: str
    scientific_basis: str | None = None

    model_config = {"from_attributes": True}
