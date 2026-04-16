"""Regenerative practice verification endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.models import Farm, Field
from cultivos.db.session import get_db
from cultivos.models.regenerative import RegenerativeScoreOut
from cultivos.services.intelligence.regenerative import compute_regenerative_score

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}",
    tags=["intelligence"],
    dependencies=[Depends(get_current_user)]
)


def _get_field(farm_id: int, field_id: int, db: Session) -> Field:
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@router.get("/regenerative-score", response_model=RegenerativeScoreOut)
def get_regenerative_score(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    """Compute how regenerative a field's management practices are.

    Score 0-100 based on: organic treatments, ancestral method usage,
    soil organic matter trend, microbiome health, and treatment diversity.
    Key for FODECIJAL: proves Cerebro drives regenerative outcomes.
    """
    field = _get_field(farm_id, field_id, db)
    result = compute_regenerative_score(field.id, db)
    return result
