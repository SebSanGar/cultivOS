"""Production scheduling API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from cultivos.db.session import get_db
from cultivos.models.production import (
    ParLevelCreate,
    ParLevelRead,
    ProductionCalendarCreate,
    ProductionCalendarDetail,
    ProductionCalendarRead,
    ProductionEntryCreate,
    ProductionEntryRead,
    ProductionEntryUpdate,
    ProductionNeed,
)
from cultivos.services import production_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Par levels
# ---------------------------------------------------------------------------

@router.post("/par-levels", response_model=ParLevelRead, status_code=201)
def set_par_level(data: ParLevelCreate, db: Session = Depends(get_db)):
    par = production_service.set_par_level(db, data)
    return ParLevelRead.model_validate(par)


@router.get("/par-levels", response_model=list[ParLevelRead])
def list_par_levels(location_id: int = Query(...), db: Session = Depends(get_db)):
    pars = production_service.list_par_levels(db, location_id)
    return [ParLevelRead.model_validate(p) for p in pars]


# ---------------------------------------------------------------------------
# Calendars
# ---------------------------------------------------------------------------

@router.post("/calendars", response_model=ProductionCalendarRead, status_code=201)
def create_calendar(data: ProductionCalendarCreate, db: Session = Depends(get_db)):
    cal = production_service.create_calendar(db, data)
    return ProductionCalendarRead.model_validate(cal)


@router.get("/calendars/{calendar_id}", response_model=ProductionCalendarDetail)
def get_calendar(calendar_id: int, db: Session = Depends(get_db)):
    cal = production_service.get_calendar(db, calendar_id)
    if not cal:
        raise HTTPException(status_code=404, detail="Calendar not found")
    return ProductionCalendarDetail(
        id=cal.id,
        location_id=cal.location_id,
        week_start_date=cal.week_start_date,
        created_at=cal.created_at,
        entries=[ProductionEntryRead.model_validate(e) for e in cal.entries],
    )


# ---------------------------------------------------------------------------
# Production entries
# ---------------------------------------------------------------------------

@router.post("/calendars/{calendar_id}/entries", response_model=ProductionEntryRead, status_code=201)
def add_entry(calendar_id: int, data: ProductionEntryCreate, db: Session = Depends(get_db)):
    entry = production_service.add_entry(db, calendar_id, data)
    if not entry:
        raise HTTPException(status_code=404, detail="Calendar not found")
    return ProductionEntryRead.model_validate(entry)


@router.patch("/production-entries/{entry_id}", response_model=ProductionEntryRead)
def update_entry(entry_id: int, data: ProductionEntryUpdate, db: Session = Depends(get_db)):
    entry = production_service.update_entry(db, entry_id, data)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return ProductionEntryRead.model_validate(entry)


# ---------------------------------------------------------------------------
# Production needs
# ---------------------------------------------------------------------------

@router.get("/production/needs", response_model=list[ProductionNeed])
def get_production_needs(location_id: int = Query(...), db: Session = Depends(get_db)):
    return production_service.get_production_needs(db, location_id)
