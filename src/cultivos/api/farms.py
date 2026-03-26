"""Farm and Field CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field
from cultivos.db.session import get_db
from cultivos.models.farm import (
    FarmCreate, FarmUpdate, FarmOut,
    FieldCreate, FieldUpdate, FieldOut,
)

router = APIRouter(prefix="/api/farms", tags=["farms"])


# ── Farm CRUD ─────────────────────────────────────────────────────────

@router.post("", response_model=FarmOut, status_code=201)
def create_farm(body: FarmCreate, db: Session = Depends(get_db)):
    farm = Farm(**body.model_dump())
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


@router.get("", response_model=list[FarmOut])
def list_farms(db: Session = Depends(get_db)):
    return db.query(Farm).order_by(Farm.created_at.desc()).all()


@router.get("/{farm_id}", response_model=FarmOut)
def get_farm(farm_id: int, db: Session = Depends(get_db)):
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm


@router.put("/{farm_id}", response_model=FarmOut)
def update_farm(farm_id: int, body: FarmUpdate, db: Session = Depends(get_db)):
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(farm, key, value)
    db.commit()
    db.refresh(farm)
    return farm


# ── Field CRUD (nested under farm) ───────────────────────────────────

@router.post("/{farm_id}/fields", response_model=FieldOut, status_code=201)
def create_field(farm_id: int, body: FieldCreate, db: Session = Depends(get_db)):
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = Field(farm_id=farm_id, **body.model_dump())
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


@router.get("/{farm_id}/fields", response_model=list[FieldOut])
def list_fields(farm_id: int, db: Session = Depends(get_db)):
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return db.query(Field).filter(Field.farm_id == farm_id).order_by(Field.created_at.desc()).all()


@router.get("/{farm_id}/fields/{field_id}", response_model=FieldOut)
def get_field(farm_id: int, field_id: int, db: Session = Depends(get_db)):
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@router.put("/{farm_id}/fields/{field_id}", response_model=FieldOut)
def update_field(farm_id: int, field_id: int, body: FieldUpdate, db: Session = Depends(get_db)):
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(field, key, value)
    db.commit()
    db.refresh(field)
    return field
