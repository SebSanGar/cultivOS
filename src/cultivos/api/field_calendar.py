"""Field crop calendar event log endpoint.

GET /api/farms/{farm_id}/fields/{field_id}/calendar?year= — returns a 12-month
timeline composing HealthScore + TreatmentRecord + FarmerObservation +
AncestralMethod event counts for a single field.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field
from cultivos.db.session import get_db
from cultivos.models.field_calendar import CalendarMonthEntry, FieldCalendarOut
from cultivos.services.intelligence.field_calendar import compute_field_calendar

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}/calendar",
    tags=["intelligence"],
)


@router.get(
    "",
    response_model=FieldCalendarOut,
    description=(
        "Composes HealthScore + TreatmentRecord + FarmerObservation + "
        "AncestralMethod (applicable_months overlap + crop match) into a "
        "12-month timeline of event counts for one field in a given year."
    ),
)
def get_field_calendar(
    farm_id: int,
    field_id: int,
    year: int | None = Query(None, ge=1900, le=3000),
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

    resolved_year = year if year is not None else datetime.utcnow().year
    result = compute_field_calendar(field, db, year=resolved_year)
    return FieldCalendarOut(
        farm_id=result["farm_id"],
        field_id=result["field_id"],
        year=result["year"],
        crop_type=result["crop_type"],
        months=[CalendarMonthEntry(**m) for m in result["months"]],
        total_events=result["total_events"],
        busiest_month=result["busiest_month"],
    )
