"""Demo data endpoints for FODECIJAL walkthrough."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field
from cultivos.db.session import get_db

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.post("/seed")
def seed_demo(db: Session = Depends(get_db)):
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
        db.query(Field)
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
