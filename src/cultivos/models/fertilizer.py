"""Pydantic schemas for the natural fertilizer knowledge base."""

from pydantic import BaseModel


class FertilizerOut(BaseModel):
    id: int
    name: str
    description_es: str
    application_method: str
    cost_per_ha_mxn: int
    nutrient_profile: str
    suitable_crops: list[str]

    model_config = {"from_attributes": True}
