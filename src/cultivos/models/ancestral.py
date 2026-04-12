"""Pydantic schemas for ancestral farming methods knowledge base."""

from pydantic import BaseModel, field_validator


class AncestralMethodOut(BaseModel):
    id: int
    name: str
    description_es: str
    region: str
    practice_type: str
    crops: list[str]
    benefits_es: str
    scientific_basis: str | None = None
    problems: list[str] = []

    model_config = {"from_attributes": True}

    @field_validator("problems", "crops", mode="before")
    @classmethod
    def _none_to_empty_list(cls, v):
        return v if v is not None else []
