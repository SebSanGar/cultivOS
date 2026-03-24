"""Waste tracking API routes."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from cultivos.db.session import get_db
from cultivos.models.waste import (
    ShelfLifeCreate,
    ShelfLifeRead,
    ShelfLifeUpdate,
    TopWastedItem,
    WasteLogCreate,
    WasteLogRead,
    WasteSummary,
)
from cultivos.services import waste_service

router = APIRouter()


@router.post("/waste", response_model=WasteLogRead, status_code=201)
def log_waste(data: WasteLogCreate, db: Session = Depends(get_db)):
    entry = waste_service.log_waste(db, data)
    return WasteLogRead.model_validate(entry)


@router.get("/waste/summary", response_model=WasteSummary)
def get_waste_summary(
    location_id: int = Query(...),
    date: datetime = Query(...),
    period: str = Query("daily"),
    db: Session = Depends(get_db),
):
    if period == "weekly":
        return waste_service.weekly_summary(db, location_id, date)
    return waste_service.daily_summary(db, location_id, date)


@router.get("/waste/top-items", response_model=list[TopWastedItem])
def get_top_wasted(
    location_id: int = Query(...),
    days: int = Query(7, ge=1),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    return waste_service.top_wasted_items(db, location_id, days, limit)


@router.get("/waste/rate")
def get_waste_rate(
    location_id: int = Query(...),
    days: int = Query(7, ge=1),
    db: Session = Depends(get_db),
):
    rate = waste_service.waste_rate(db, location_id, days)
    return {"location_id": location_id, "days": days, "total_waste_cost": rate}


# ---------------------------------------------------------------------------
# Shelf life tracking
# ---------------------------------------------------------------------------

@router.post("/batches", response_model=ShelfLifeRead, status_code=201)
def create_batch(data: ShelfLifeCreate, db: Session = Depends(get_db)):
    batch = waste_service.create_batch(db, data)
    return ShelfLifeRead.model_validate(batch)


@router.get("/batches/expiring", response_model=list[ShelfLifeRead])
def get_expiring(
    location_id: int = Query(...),
    hours: int = Query(6, ge=1),
    db: Session = Depends(get_db),
):
    batches = waste_service.get_expiring_batches(db, location_id, hours)
    return [ShelfLifeRead.model_validate(b) for b in batches]


@router.patch("/batches/{batch_id}", response_model=ShelfLifeRead)
def update_batch(batch_id: int, data: ShelfLifeUpdate, db: Session = Depends(get_db)):
    batch = waste_service.update_batch(db, batch_id, data)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return ShelfLifeRead.model_validate(batch)
