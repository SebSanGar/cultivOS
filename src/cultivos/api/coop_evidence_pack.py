"""Cooperative FODECIJAL evidence pack endpoint (task #208).

GET /api/cooperatives/{coop_id}/evidence-pack — single-call grant-ready rollup
composing 6 existing intelligence services.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Cooperative
from cultivos.db.session import get_db
from cultivos.models.coop_evidence_pack import CoopEvidencePackOut
from cultivos.services.intelligence.coop_evidence_pack import (
    compute_coop_evidence_pack,
)

router = APIRouter(
    prefix="/api/cooperatives/{coop_id}/evidence-pack",
    tags=["intelligence"],
)


@router.get(
    "",
    response_model=CoopEvidencePackOut,
    description=(
        "FODECIJAL grant-ready evidence rollup — composes readiness, portfolio "
        "health, carbon sequestration, disease outbreak risk, regenerative "
        "adoption, and crop diversity for a cooperative into one endpoint."
    ),
)
def get_coop_evidence_pack(coop_id: int, db: Session = Depends(get_db)):
    coop = db.query(Cooperative).filter(Cooperative.id == coop_id).first()
    if not coop:
        raise HTTPException(status_code=404, detail="Cooperative not found")
    result = compute_coop_evidence_pack(coop, db)
    return CoopEvidencePackOut(**result)
