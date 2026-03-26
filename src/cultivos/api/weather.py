"""Weather CRUD endpoints — nested under /api/farms/{farm_id}/weather."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, WeatherRecord
from cultivos.db.session import get_db
from cultivos.models.weather import WeatherRecordCreate, WeatherRecordOut

router = APIRouter(
    prefix="/api/farms/{farm_id}/weather",
    tags=["weather"],
)


def _get_farm(farm_id: int, db: Session) -> Farm:
    """Validate farm exists."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm


@router.post("", response_model=WeatherRecordOut, status_code=201)
def create_weather_record(
    farm_id: int,
    body: WeatherRecordCreate,
    db: Session = Depends(get_db),
):
    _get_farm(farm_id, db)
    record = WeatherRecord(
        farm_id=farm_id,
        temp_c=body.temp_c,
        humidity_pct=body.humidity_pct,
        wind_kmh=body.wind_kmh,
        description=body.description,
        forecast_3day=[day.model_dump() for day in body.forecast_3day],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=list[WeatherRecordOut])
def list_weather_records(
    farm_id: int,
    db: Session = Depends(get_db),
):
    _get_farm(farm_id, db)
    return (
        db.query(WeatherRecord)
        .filter(WeatherRecord.farm_id == farm_id)
        .order_by(WeatherRecord.recorded_at.desc())
        .all()
    )
