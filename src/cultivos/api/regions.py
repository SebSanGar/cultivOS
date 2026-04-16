"""Region profile endpoints — surface region-specific agricultural context.

Exposes the pure region metadata resolver (services/intelligence/regions.py)
over HTTP so frontend pages and grant reviewers can inspect region-aware
context (climate, soil, crops, currency) without touching service internals.
"""

from fastapi import APIRouter, Depends, HTTPException

from cultivos.auth import get_current_user
from cultivos.models.region import RegionListItem, RegionProfileOut
from cultivos.services.intelligence.regions import _PROFILES

router = APIRouter(prefix="/api/regions", tags=["regions"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[RegionListItem])
def list_regions():
    """List all known agricultural regions with their key, display name, and currency."""
    return [
        RegionListItem(key=key, region_name=profile["region_name"], currency=profile["currency"])
        for key, profile in _PROFILES.items()
    ]


@router.get("/{region}", response_model=RegionProfileOut)
def get_region(region: str):
    """Return the full agricultural profile for a known region key (e.g. jalisco_mx)."""
    key = region.lower().strip()
    profile = _PROFILES.get(key)
    if profile is None:
        raise HTTPException(status_code=404, detail="Region not found")
    return RegionProfileOut(**profile)
