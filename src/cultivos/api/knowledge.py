"""Knowledge base endpoints — fertilizers, ancestral methods, etc."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from cultivos.db.models import AgronomistTip, AncestralMethod, CropType, CropVariety, Fertilizer
from cultivos.db.session import get_db
from cultivos.models.agronomist_tip import AgronomistTipOut
from cultivos.models.ancestral import AncestralMethodOut
from cultivos.models.crop_type import CropTypeOut
from cultivos.models.crop_variety import CropVarietyOut
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


@router.get("/search")
def search_knowledge(
    q: str = Query("", description="Search term — matches name, description, tip text (case-insensitive)"),
    limit: int = Query(20, ge=1, le=200, description="Maximum results to return"),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Full-text search across ancestral methods, fertilizers, and agronomist tips.

    Returns list of {type, id, name, summary} sorted with exact name matches first.
    Unknown term returns empty list — never 404.
    """
    term = q.lower().strip()
    results: list[dict] = []

    # Ancestral methods — search name + description_es + benefits_es
    ancestral = db.query(AncestralMethod).all()
    for m in ancestral:
        searchable = " ".join([
            m.name or "",
            m.description_es or "",
            m.benefits_es or "",
        ]).lower()
        if not term or term in searchable:
            results.append({
                "type": "ancestral_method",
                "id": m.id,
                "name": m.name,
                "summary": (m.description_es or "")[:120],
                "_exact": term and term in (m.name or "").lower(),
            })

    # Fertilizers — search name + description_es
    fertilizers = db.query(Fertilizer).all()
    for f in fertilizers:
        searchable = " ".join([
            f.name or "",
            f.description_es or "",
        ]).lower()
        if not term or term in searchable:
            results.append({
                "type": "fertilizer",
                "id": f.id,
                "name": f.name,
                "summary": (f.description_es or "")[:120],
                "_exact": term and term in (f.name or "").lower(),
            })

    # Agronomist tips — search tip_text_es + crop + problem
    tips = db.query(AgronomistTip).all()
    for t in tips:
        searchable = " ".join([
            t.tip_text_es or "",
            t.crop or "",
            t.problem or "",
        ]).lower()
        if not term or term in searchable:
            results.append({
                "type": "agronomist_tip",
                "id": t.id,
                "name": f"{t.crop} — {t.problem}",
                "summary": (t.tip_text_es or "")[:120],
                "_exact": False,
            })

    # Sort: exact name matches first
    results.sort(key=lambda r: (0 if r["_exact"] else 1))
    # Strip internal sort key and apply limit
    cleaned = [{"type": r["type"], "id": r["id"], "name": r["name"], "summary": r["summary"]} for r in results]
    return cleaned[:limit]


@router.get("/crops/{crop_name}/varieties", response_model=list[CropVarietyOut])
def list_crop_varieties(
    crop_name: str,
    db: Session = Depends(get_db),
):
    """Return local Jalisco/LATAM varieties for a given crop. 404 if crop has no registered varieties."""
    crop_lower = crop_name.lower()
    varieties = db.query(CropVariety).filter(
        CropVariety.crop_name == crop_lower
    ).all()
    if not varieties:
        raise HTTPException(
            status_code=404,
            detail=f"No varieties found for crop '{crop_name}'",
        )
    return varieties


@router.get("/agronomist-tips", response_model=list[AgronomistTipOut])
def list_agronomist_tips(
    crop: str | None = Query(None, description="Filter by crop (e.g. maiz, agave, frijol, chile)"),
    problem: str | None = Query(None, description="Filter by problem (e.g. drought, disease, nutrient_deficiency, water_stress)"),
    db: Session = Depends(get_db),
):
    """List agronomist tips for Jalisco crops, optionally filtered by crop and/or problem."""
    query = db.query(AgronomistTip)
    if crop:
        query = query.filter(AgronomistTip.crop == crop.lower())
    if problem:
        query = query.filter(AgronomistTip.problem == problem.lower())
    return query.all()
