"""Field weather alert history endpoint (#209).

GET /api/farms/{farm_id}/fields/{field_id}/weather-alert-history?days=90
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field
from cultivos.db.session import get_db
from cultivos.models.field_weather_alert_history import (
    FieldWeatherAlertHistoryOut,
    WeatherAlertTypeSummary,
)
from cultivos.services.intelligence.field_weather_alert_history import (
    compute_field_weather_alert_history,
)

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}/weather-alert-history",
    tags=["intelligence"],
)


@router.get(
    "",
    response_model=FieldWeatherAlertHistoryOut,
    description=(
        "Aggregate severe-weather alert history for a field over the window. "
        "Per-type counts, dominant severity, most-frequent type, alerts/month "
        "average, and first-half vs second-half trend."
    ),
)
def get_field_weather_alert_history(
    farm_id: int,
    field_id: int,
    days: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db),
):
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = (
        db.query(Field)
        .filter(Field.id == field_id, Field.farm_id == farm_id)
        .first()
    )
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    result = compute_field_weather_alert_history(
        farm_id=farm_id, period_days=days, db=db
    )
    return FieldWeatherAlertHistoryOut(
        field_id=field_id,
        period_days=result["period_days"],
        total_alerts=result["total_alerts"],
        by_type=[WeatherAlertTypeSummary(**row) for row in result["by_type"]],
        most_frequent_type=result["most_frequent_type"],
        alerts_per_month_avg=result["alerts_per_month_avg"],
        trend=result["trend"],
    )
