"""Public farm list — no auth required.

Exposes only {id, name, municipality} for the registration dropdown.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from cultivos.db.models import Farm
from cultivos.db.session import get_db

router = APIRouter(prefix="/api/farms/public", tags=["farms-public"])


class FarmPublicOut(BaseModel):
    id: int
    name: str
    municipality: str | None = None


@router.get("", response_model=list[FarmPublicOut], description="List farms with minimal fields for registration dropdown. No auth required.")
def list_farms_public(db: Session = Depends(get_db)):
    farms = db.query(Farm.id, Farm.name, Farm.municipality).order_by(Farm.name).all()
    return [FarmPublicOut(id=f.id, name=f.name, municipality=f.municipality) for f in farms]
