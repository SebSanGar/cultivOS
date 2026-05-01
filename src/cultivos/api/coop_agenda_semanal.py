"""Thin route for cooperative weekly agenda endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Cooperative
from cultivos.db.session import get_db
from cultivos.models.coop_agenda_semanal import AgendaSemanalOut
from cultivos.services.intelligence.coop_agenda_semanal import compute_coop_agenda_semanal

router = APIRouter(prefix="/api/cooperatives", tags=["cooperatives"])


@router.get("/{coop_id}/agenda-semanal", response_model=AgendaSemanalOut)
def get_agenda_semanal(coop_id: int, db: Session = Depends(get_db)):
    """Top 5 stressed fields across cooperative with Spanish action sentences."""
    coop = db.query(Cooperative).get(coop_id)
    if not coop:
        raise HTTPException(status_code=404, detail="Cooperative not found")
    return compute_coop_agenda_semanal(coop, db)
