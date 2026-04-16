"""Drone flight logging endpoints — nested under /api/farms/{farm_id}/fields/{field_id}/flights."""

from collections import Counter

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.models import Farm, Field, FlightLog
from cultivos.db.session import get_db
from cultivos.models.flight import FlightLogCreate, FlightLogOut, FlightStatsOut

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}/flights",
    tags=["flights"],
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


@router.get("/stats", response_model=FlightStatsOut)
def flight_stats(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    """Aggregated flight statistics for a field."""
    _get_field(farm_id, field_id, db)
    flights = db.query(FlightLog).filter(FlightLog.field_id == field_id).all()

    total_minutes = sum(f.duration_minutes or 0 for f in flights)
    total_area = sum(f.coverage_pct or 0 for f in flights)
    drone_counts = Counter(f.drone_type for f in flights)

    return FlightStatsOut(
        total_flights=len(flights),
        total_hours=round(total_minutes / 60, 2) if flights else 0,
        total_area_covered_ha=round(total_area, 2),
        drone_breakdown=dict(drone_counts),
    )


@router.post("", response_model=FlightLogOut, status_code=201)
def log_flight(
    farm_id: int,
    field_id: int,
    body: FlightLogCreate,
    db: Session = Depends(get_db),
):
    """Record a new drone flight."""
    _get_field(farm_id, field_id, db)

    flight = FlightLog(
        field_id=field_id,
        drone_type=body.drone_type,
        mission_type=body.mission_type,
        flight_date=body.flight_date,
        duration_minutes=body.duration_minutes,
        altitude_m=body.altitude_m,
        images_count=body.images_count,
        coverage_pct=body.coverage_pct,
        s3_path=body.s3_path,
    )
    db.add(flight)
    db.commit()
    db.refresh(flight)
    return flight


@router.get("", response_model=list[FlightLogOut])
def list_flights(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    """List all flights for a field, most recent first."""
    _get_field(farm_id, field_id, db)
    return (
        db.query(FlightLog)
        .filter(FlightLog.field_id == field_id)
        .order_by(FlightLog.flight_date.desc())
        .all()
    )
