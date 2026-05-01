"""Thin route for cooperative monthly summary endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Cooperative
from cultivos.db.session import get_db
from cultivos.models.coop_resumen_mensual import ResumenMensualOut
from cultivos.services.intelligence.coop_resumen_mensual import compute_coop_resumen_mensual

router = APIRouter(prefix="/api/cooperatives", tags=["cooperatives"])


@router.get("/{coop_id}/resumen-mensual", response_model=ResumenMensualOut)
def get_resumen_mensual(coop_id: int, db: Session = Depends(get_db)):
    """Last 30-day cooperative summary in Spanish."""
    coop = db.query(Cooperative).get(coop_id)
    if not coop:
        raise HTTPException(status_code=404, detail="Cooperative not found")
    return compute_coop_resumen_mensual(coop, db)
