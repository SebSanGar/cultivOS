"""Knowledge base endpoints — fertilizers, ancestral methods, etc."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from cultivos.db.models import AncestralMethod, Fertilizer
from cultivos.db.session import get_db
from cultivos.models.ancestral import AncestralMethodOut
from cultivos.models.fertilizer import FertilizerOut

router = APIRouter(
    prefix="/api/knowledge",
    tags=["knowledge"],
)


@router.get("/fertilizers", response_model=list[FertilizerOut])
def list_fertilizers(
    crop: str | None = Query(None, description="Filter by suitable crop type (e.g. maiz, agave)"),
    db: Session = Depends(get_db),
):
    """List all natural fertilizer methods, optionally filtered by crop type."""
    query = db.query(Fertilizer)
    if crop:
        # JSON array filter — SQLite uses json_each for array containment
        query = query.filter(
            Fertilizer.suitable_crops.contains(crop)
        )
    results = query.all()
    if crop:
        # Double-check filtering since SQLite JSON support varies
        results = [f for f in results if crop in (f.suitable_crops or [])]
    return results


@router.get("/ancestral", response_model=list[AncestralMethodOut])
def list_ancestral_methods(
    region: str | None = Query(None, description="Filter by region (e.g. jalisco, mesoamerica)"),
    type: str | None = Query(None, alias="type", description="Filter by practice type (e.g. soil_management, intercropping)"),
    db: Session = Depends(get_db),
):
    """List ancestral farming methods, optionally filtered by region or practice type."""
    query = db.query(AncestralMethod)
    if type:
        query = query.filter(AncestralMethod.practice_type == type)
    results = query.all()
    if region:
        region_lower = region.lower()
        results = [m for m in results if region_lower in m.region.lower()]
    return results
