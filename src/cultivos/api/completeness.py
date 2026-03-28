"""Data completeness scoring endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.session import get_db
from cultivos.services.intelligence.completeness import compute_data_completeness

router = APIRouter(
    prefix="/api/farms/{farm_id}/data-completeness",
    tags=["completeness"],
)


@router.get("")
def get_data_completeness(farm_id: int, db: Session = Depends(get_db)):
    """Return data completeness scores for a farm and its fields."""
    try:
        return compute_data_completeness(db, farm_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Farm not found")
