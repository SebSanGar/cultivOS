"""Disease/pest identification endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from cultivos.db.models import Disease
from cultivos.db.session import get_db
from cultivos.models.disease import DiseaseMatch, DiseaseOut, IdentifyRequest
from cultivos.services.crop.disease import identify_diseases

router = APIRouter(
    prefix="/api/knowledge/diseases",
    tags=["diseases"],
)


@router.get("", response_model=list[DiseaseOut])
def list_diseases(
    crop: str | None = Query(None, description="Filter by affected crop (e.g. maiz, tomate)"),
    db: Session = Depends(get_db),
):
    """List all known diseases/pests, optionally filtered by crop."""
    query = db.query(Disease)
    results = query.all()
    if crop:
        crop_lower = crop.lower()
        results = [d for d in results if crop_lower in [c.lower() for c in (d.affected_crops or [])]]
    return results


@router.post("/identify", response_model=list[DiseaseMatch])
def identify_disease(
    request: IdentifyRequest,
    db: Session = Depends(get_db),
):
    """Identify diseases from reported symptoms. Returns ranked matches with confidence scores."""
    all_diseases = db.query(Disease).all()
    disease_dicts = [
        {
            "id": d.id,
            "name": d.name,
            "description_es": d.description_es,
            "symptoms": d.symptoms or [],
            "affected_crops": d.affected_crops or [],
            "treatments": d.treatments or [],
            "region": d.region,
            "severity": d.severity,
        }
        for d in all_diseases
    ]
    matches = identify_diseases(
        symptoms=request.symptoms,
        diseases=disease_dicts,
        crop=request.crop,
    )
    return matches
