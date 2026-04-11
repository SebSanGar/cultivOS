"""Pydantic schemas for farmer vocabulary knowledge base."""

from pydantic import BaseModel


class FarmerVocabularyOut(BaseModel):
    id: int
    phrase: str
    formal_term_es: str
    likely_cause: str
    recommended_action: str
    crop: str | None = None
    symptom: str | None = None

    model_config = {"from_attributes": True}
