"""Demo data endpoints for FODECIJAL walkthrough."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from cultivos.auth import require_role
from cultivos.db.models import Farm, Field as FieldORM
from cultivos.db.session import get_db
from cultivos.services.intelligence.farmer_query import simulate_farmer_query

router = APIRouter(prefix="/api/demo", tags=["demo"])


class FarmerQueryIn(BaseModel):
    message: str = Field(..., min_length=1)
    farm_id: Optional[int] = None


class FarmerQueryOut(BaseModel):
    detected_issue: str
    crop: Optional[str]
    severity: str
    recommended_action: str
    confidence: float


@router.post("/seed")
def seed_demo(db: Session = Depends(get_db), _user=Depends(require_role("admin"))):
    """Seed the database with realistic Jalisco demo data. Idempotent."""
    from scripts.seed_demo import seed_demo_data, _demo_exists, DEMO_MARKER

    if _demo_exists(db):
        return JSONResponse(
            status_code=200,
            content={"message": "Demo data already exists"},
        )

    seed_demo_data(db)
    farms = db.query(Farm).filter(Farm.name.contains(DEMO_MARKER)).count()
    fields = (
        db.query(FieldORM)
        .join(Farm)
        .filter(Farm.name.contains(DEMO_MARKER))
        .count()
    )
    return JSONResponse(
        status_code=201,
        content={"farms": farms, "fields": fields, "message": "Demo data seeded"},
    )


@router.get("/farms")
def get_demo_farms(db: Session = Depends(get_db)):
    """Return only [DEMO] farms with their fields for the walkthrough page."""
    farms = db.query(Farm).filter(Farm.name.contains("[DEMO]")).all()
    return [
        {
            "id": f.id,
            "name": f.name,
            "owner_name": f.owner_name,
            "municipality": f.municipality,
            "total_hectares": f.total_hectares,
            "location_lat": f.location_lat,
            "location_lon": f.location_lon,
            "fields": [
                {
                    "id": field.id,
                    "name": field.name,
                    "crop_type": field.crop_type,
                    "hectares": field.hectares,
                }
                for field in f.fields
            ],
        }
        for f in farms
    ]


@router.post("/farmer-query", response_model=FarmerQueryOut)
def farmer_query(payload: FarmerQueryIn, db: Session = Depends(get_db)):
    """Simulate a WhatsApp AI response to a Spanish farming query.

    Accepts a farmer message in Spanish and an optional farm_id.
    Returns a structured AI response with detected issue, crop, severity,
    recommended organic action (in Spanish), and confidence score.
    """
    crop_hint: Optional[str] = None

    if payload.farm_id is not None:
        farm = db.query(Farm).filter(Farm.id == payload.farm_id).first()
        if farm is None:
            raise HTTPException(status_code=404, detail="Farm not found")
        # Use the crop type of the first field as a hint
        first_field = (
            db.query(FieldORM)
            .filter(FieldORM.farm_id == farm.id)
            .first()
        )
        if first_field:
            crop_hint = first_field.crop_type

    result = simulate_farmer_query(message=payload.message, crop_hint=crop_hint)
    return FarmerQueryOut(**result)
