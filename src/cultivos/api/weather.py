"""Weather CRUD endpoints — nested under /api/farms/{farm_id}/weather."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.models import Farm, WeatherRecord
from cultivos.db.session import get_db
from cultivos.models.weather import WeatherAlertsResponse, WeatherRecordCreate, WeatherRecordOut
from cultivos.services.intelligence.weather_alerts import detect_weather_alerts

router = APIRouter(
    prefix="/api/farms/{farm_id}/weather",
    tags=["weather"],
    dependencies=[Depends(get_current_user)]
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
    """Record a new weather observation for a farm, including current conditions and 3-day forecast."""
    _get_farm(farm_id, db)
    record = WeatherRecord(
        farm_id=farm_id,
        temp_c=body.temp_c,
        humidity_pct=body.humidity_pct,
        wind_kmh=body.wind_kmh,
        rainfall_mm=body.rainfall_mm,
        description=body.description,
        forecast_3day=[day.model_dump() for day in body.forecast_3day],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/alerts", response_model=WeatherAlertsResponse)
def get_weather_alerts(
    farm_id: int,
    db: Session = Depends(get_db),
):
    """Check latest weather data for severe conditions and return warnings.

    Thresholds: frost (<2C), extreme heat (>38C), heavy rain (>50mm),
    high wind (>60km/h), hail (description keywords).
    """
    _get_farm(farm_id, db)
    latest = (
        db.query(WeatherRecord)
        .filter(WeatherRecord.farm_id == farm_id)
        .order_by(WeatherRecord.recorded_at.desc())
        .first()
    )
    if not latest:
        return WeatherAlertsResponse(farm_id=farm_id, alerts=[], weather_record_id=None)

    raw_alerts = detect_weather_alerts(
        temp_c=latest.temp_c,
        humidity_pct=latest.humidity_pct,
        wind_kmh=latest.wind_kmh,
        rainfall_mm=latest.rainfall_mm,
        description=latest.description,
        forecast_3day=latest.forecast_3day or [],
    )
    return WeatherAlertsResponse(
        farm_id=farm_id,
        alerts=raw_alerts,
        weather_record_id=latest.id,
    )


@router.get("", response_model=list[WeatherRecordOut])
def list_weather_records(
    farm_id: int,
    db: Session = Depends(get_db),
):
    """Return all weather records for a farm, ordered by most recent first."""
    _get_farm(farm_id, db)
    return (
        db.query(WeatherRecord)
        .filter(WeatherRecord.farm_id == farm_id)
        .order_by(WeatherRecord.recorded_at.desc())
        .all()
    )
