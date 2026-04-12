"""Global fields endpoint — GET /api/fields for cross-farm field queries."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from cultivos.db.models import Field
from cultivos.db.session import get_db
from cultivos.models.farm import FieldOut

router = APIRouter(prefix="/api/fields", tags=["fields"])


@router.get("", response_model=list[FieldOut])
def list_all_fields(
    crop_type: Optional[str] = Query(None, description="Filter by crop type"),
    db: Session = Depends(get_db),
):
    """List all fields across all farms, optionally filtered by crop type."""
    q = db.query(Field)
    if crop_type:
        q = q.filter(Field.crop_type == crop_type)
    return q.order_by(Field.id).all()
