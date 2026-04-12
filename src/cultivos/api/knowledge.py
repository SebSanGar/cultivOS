"""Knowledge base endpoints — fertilizers, ancestral methods, etc."""

from datetime import datetime
from typing import Optional

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from cultivos.db.models import AgronomistTip, AncestralMethod, CropType, CropVariety, FarmerVocabulary, Fertilizer

_VALID_TYPES = {"vocab", "tips", "fertilizers", "ancestral"}
from cultivos.db.session import get_db
from cultivos.models.agronomist_tip import AgronomistTipOut
from cultivos.models.ancestral import AncestralMethodOut
from cultivos.models.tek_calendar import TEKCalendarEntryOut
from cultivos.models.crop_type import CropTypeOut
from cultivos.models.crop_variety import CropVarietyOut
from cultivos.models.farmer_vocabulary import FarmerVocabularyOut
from cultivos.models.fertilizer import FertilizerOut
from cultivos.models.treatment_outcomes import TreatmentOutcomeItem
from cultivos.models.treatment_success_rates import TreatmentSuccessRateItem
from cultivos.services.intelligence.treatment_outcomes import compute_treatment_outcomes
from cultivos.services.intelligence.treatment_success_rates import compute_treatment_success_rates

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


@router.get("/tek-calendar", response_model=list[TEKCalendarEntryOut])
def tek_calendar(
    month: int = Query(..., ge=1, le=12, description="Month number (1-12)"),
    crop_type: str | None = Query(None, description="Filter by crop type (e.g. maiz, agave)"),
    db: Session = Depends(get_db),
):
    """Return ancestral/TEK practices recommended for the given month, sorted by ecological benefit."""
    methods = db.query(AncestralMethod).all()

    # Filter by applicable_months — Python-side for JSON portability
    results = [
        m for m in methods
        if m.applicable_months and month in m.applicable_months
    ]

    if crop_type:
        crop_lower = crop_type.lower()
        results = [m for m in results if m.crops and crop_lower in [c.lower() for c in m.crops]]

    # Sort by ecological_benefit DESC (None treated as 0)
    results.sort(key=lambda m: m.ecological_benefit or 0, reverse=True)

    return [
        TEKCalendarEntryOut(
            method_name=m.name,
            description_es=m.description_es,
            timing_rationale=m.timing_rationale,
            crop_types=m.crops or [],
            ecological_benefit=m.ecological_benefit,
        )
        for m in results
    ]


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
    type: Optional[str] = Query(None, description="Filter by category: vocab | tips | fertilizers | ancestral"),
    limit: int = Query(20, ge=1, le=200, description="Maximum results to return"),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Full-text search across farmer vocabulary, ancestral methods, fertilizers, and agronomist tips.

    Returns list of {type, id, name, summary} sorted with exact name matches first.
    Unknown term returns empty list — never 404. Invalid type returns 422.
    """
    from fastapi import HTTPException as _HTTPException
    if type is not None and type not in _VALID_TYPES:
        raise _HTTPException(status_code=422, detail=f"Invalid type '{type}'. Must be one of: {sorted(_VALID_TYPES)}")

    term = q.lower().strip()
    results: list[dict] = []

    # Farmer vocabulary — search phrase + formal_term_es
    if type is None or type == "vocab":
        vocab = db.query(FarmerVocabulary).all()
        for v in vocab:
            searchable = " ".join([
                v.phrase or "",
                v.formal_term_es or "",
            ]).lower()
            if not term or term in searchable:
                results.append({
                    "type": "farmer_vocabulary",
                    "id": v.id,
                    "name": v.phrase,
                    "summary": (v.formal_term_es or "")[:120],
                    "_exact": term and term in (v.phrase or "").lower(),
                })

    # Ancestral methods — search name + description_es + benefits_es
    if type is None or type == "ancestral":
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
    if type is None or type == "fertilizers":
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
    if type is None or type == "tips":
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


@router.get("/crop-varieties", response_model=list[CropVarietyOut])
def search_crop_varieties(
    crop: str = Query(..., description="Crop name (e.g. maiz, agave, frijol)"),
    region: str | None = Query(None, description="Region filter — case-insensitive substring match"),
    altitude_m: int | None = Query(None, description="Target altitude in metres — returns varieties within ±500m"),
    db: Session = Depends(get_db),
):
    """Search crop varieties by crop type, optional region, and optional altitude range.

    Returns empty list when no matches found (never 404).
    Results sorted by water_mm ASC (most drought-efficient first).
    """
    query = db.query(CropVariety).filter(CropVariety.crop_name == crop.lower())

    if region is not None:
        query = query.filter(CropVariety.region.ilike(f"%{region}%"))

    if altitude_m is not None:
        query = query.filter(
            CropVariety.altitude_m >= altitude_m - 500,
            CropVariety.altitude_m <= altitude_m + 500,
        )

    varieties = query.order_by(
        CropVariety.water_mm.is_(None),  # nulls last
        CropVariety.water_mm.asc(),
    ).all()

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


@router.get("/farmer-vocabulary", response_model=list[FarmerVocabularyOut])
def list_farmer_vocabulary(
    crop: str | None = Query(None, description="Filter by crop (e.g. maiz, agave, frijol)"),
    symptom: str | None = Query(None, description="Filter by symptom category (e.g. yellowing, pest, drought, dying, disease)"),
    db: Session = Depends(get_db),
):
    """Return Jalisco farmer colloquial phrases mapped to formal agronomic terms and recommended actions.

    Unknown crop/symptom combination returns empty list — never 404.
    Case-insensitive matching on crop and symptom.
    """
    results = db.query(FarmerVocabulary).all()
    if crop:
        crop_lower = crop.lower()
        results = [r for r in results if r.crop is None or r.crop.lower() == crop_lower]
    if symptom:
        symptom_lower = symptom.lower()
        results = [r for r in results if r.symptom and r.symptom.lower() == symptom_lower]
    return results


@router.get("/treatment-outcomes", response_model=list[TreatmentOutcomeItem])
def get_treatment_outcomes(
    crop_type: Optional[str] = Query(None, description="Filter by crop type (e.g. maiz, agave)"),
    start_date: Optional[datetime] = Query(None, description="Filter treatments on or after this date (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="Filter treatments on or before this date (ISO 8601)"),
    db: Session = Depends(get_db),
):
    """Per-crop treatment effectiveness summary.

    For each (crop_type, problema) pair, returns the average health improvement
    observed within 30 days of applying that treatment. Only treatments with a
    follow-up HealthScore are included. Sorted by avg_health_delta descending.
    """
    return compute_treatment_outcomes(db, crop_type=crop_type, start_date=start_date, end_date=end_date)


@router.get("/treatment-success-rates", response_model=list[TreatmentSuccessRateItem])
def get_treatment_success_rates(
    crop_type: Optional[str] = Query(None, description="Filter by crop type (e.g. maiz, agave)"),
    db: Session = Depends(get_db),
):
    """Organic treatment success rates per (crop_type, problema).

    Aggregates TreatmentRecord + 30-day HealthScore follow-up. Returns the
    percentage of treatments that produced a positive health delta, alongside
    the average delta and total count. Sorted by success_rate_pct descending.
    """
    return compute_treatment_success_rates(db, crop_type=crop_type)

