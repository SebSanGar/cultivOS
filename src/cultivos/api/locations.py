"""Location API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.session import get_db
from cultivos.db.models import Location
from cultivos.models.location import LocationCreate, LocationRead

router = APIRouter()


@router.post("/locations", response_model=LocationRead, status_code=201)
def create_location(data: LocationCreate, db: Session = Depends(get_db)):
    loc = Location(
        name=data.name,
        address=data.address,
        timezone=data.timezone,
        currency=data.currency,
    )
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return LocationRead.model_validate(loc)


@router.get("/locations", response_model=list[LocationRead])
def list_locations(db: Session = Depends(get_db)):
    locations = db.query(Location).filter(Location.deleted_at.is_(None)).all()
    return [LocationRead.model_validate(loc) for loc in locations]


@router.get("/locations/{location_id}", response_model=LocationRead)
def get_location(location_id: int, db: Session = Depends(get_db)):
    loc = db.query(Location).filter(
        Location.id == location_id, Location.deleted_at.is_(None)
    ).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    return LocationRead.model_validate(loc)
