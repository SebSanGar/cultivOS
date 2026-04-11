"""Knowledge base endpoints — fertilizers, ancestral methods, etc."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from cultivos.db.models import AncestralMethod, CropType, Fertilizer
from cultivos.db.session import get_db
from cultivos.models.ancestral import AncestralMethodOut
from cultivos.models.crop_type import CropTypeOut
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


@router.get("/crops", response_model=list[CropTypeOut])
def list_crops(
    region: str | None = Query(None, description="Filter by growing region (e.g. jalisco, ontario)"),
    db: Session = Depends(get_db),
):
    """List all crop types, optionally filtered by growing region."""
    results = db.query(CropType).all()
    if region:
        region_lower = region.lower()
        results = [c for c in results if region_lower in [r.lower() for r in (c.regions or [])]]
    return results


@router.get("/ancestral", response_model=list[AncestralMethodOut])
def list_ancestral_methods(
    region: str | None = Query(None, description="Filter by region (e.g. jalisco, mesoamerica)"),
    type: str | None = Query(None, alias="type", description="Filter by practice type (e.g. soil_management, intercropping)"),
    problem: str | None = Query(None, description="Filter by problem the method addresses (e.g. compaction, erosion)"),
    crop: str | None = Query(None, description="Filter by compatible crop (e.g. maiz, agave)"),
    db: Session = Depends(get_db),
):
    """List ancestral farming methods, optionally filtered by region, practice type, problem, or crop."""
    query = db.query(AncestralMethod)
    if type:
        query = query.filter(AncestralMethod.practice_type == type)
    results = query.all()
    if region:
        region_lower = region.lower()
        results = [m for m in results if region_lower in m.region.lower()]
    if problem:
        problem_lower = problem.lower()
        results = [m for m in results if m.problems and problem_lower in [p.lower() for p in m.problems]]
    if crop:
        crop_lower = crop.lower()
        results = [m for m in results if m.crops and crop_lower in [c.lower() for c in m.crops]]
    return results
