"""Pydantic schemas for the natural fertilizer knowledge base."""

from pydantic import BaseModel


class FertilizerOut(BaseModel):
    id: int
    name: str
    name_en: str | None = None
    description_es: str
    description_en: str | None = None
    application_method: str
    application_method_en: str | None = None
    cost_per_ha_mxn: int
    nutrient_profile: str
    nutrient_profile_en: str | None = None
    suitable_crops: list[str]

    model_config = {"from_attributes": True}
