"""Seasonal TEK calendar alerts endpoint — nested under /api/farms/{farm_id}."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from cultivos.db.models import Farm
from cultivos.db.session import get_db
from cultivos.models.seasonal_alert import SeasonalAlertOut, SeasonalAlertsResponse
from cultivos.services.intelligence.seasonal_calendar import (
    _classify_current_season,
    generate_seasonal_alerts,
)

router = APIRouter(
    prefix="/api/farms/{farm_id}",
    tags=["seasonal-alerts"],
)


def _get_farm(farm_id: int, db: Session) -> Farm:
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm


@router.get("/seasonal-alerts", response_model=SeasonalAlertsResponse)
def get_seasonal_alerts(
    farm_id: int,
    reference_date: Optional[date] = Query(default=None, description="Override date (defaults to today)"),
    db: Session = Depends(get_db),
):
    """Get seasonal TEK calendar alerts for a farm.

    Returns active planting, preparation, harvest, and maintenance
    windows based on Jalisco phenology and ancestral traditions.
    """
    _get_farm(farm_id, db)

    ref = reference_date or date.today()
    alerts = generate_seasonal_alerts(reference_date=ref)
    season = _classify_current_season(ref.month)

    return SeasonalAlertsResponse(
        farm_id=farm_id,
        season=season,
        reference_date=ref.isoformat(),
        alerts=[SeasonalAlertOut(**a) for a in alerts],
    )
