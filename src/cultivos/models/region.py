"""Pydantic schemas for region profile endpoint."""

from pydantic import BaseModel


class RegionProfileOut(BaseModel):
    """Agricultural profile for a known region (climate, soil, crops, currency)."""

    region_name: str
    climate_zone: str
    soil_type: str
    growing_season: str
    key_crops: list[str]
    currency: str
    seasonal_notes: str


class RegionListItem(BaseModel):
    """Lightweight region entry for listing endpoint."""

    key: str
    region_name: str
    currency: str
