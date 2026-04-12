"""Field pest/disease history summary endpoint (#204).

GET /api/farms/{farm_id}/fields/{field_id}/disease-history?months=12 —
aggregates disease-risk triggers by month over weather + NDVI + soil data.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field
from cultivos.db.session import get_db
from cultivos.models.field_disease_history import FieldDiseaseHistoryOut
from cultivos.services.intelligence.field_disease_history import (
    compute_field_disease_history,
)

router = APIRouter(tags=["intelligence"])


@router.get(
    "/api/farms/{farm_id}/fields/{field_id}/disease-history",
    response_model=FieldDiseaseHistoryOut,
    description=(
        "Field pest/disease history — aggregates trigger-based disease risk "
        "by month over the last N months. Returns per-month triggers + diseases, "
        "disease counts, recurrence detection, and months-disease-free."
    ),
)
def get_field_disease_history(
    farm_id: int,
    field_id: int,
    months: int = Query(default=12, ge=1, le=60),
    db: Session = Depends(get_db),
):
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    field = (
        db.query(Field)
        .filter(Field.id == field_id, Field.farm_id == farm_id)
        .first()
    )
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    return compute_field_disease_history(field, db, months=months)
