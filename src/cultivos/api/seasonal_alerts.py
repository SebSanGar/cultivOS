"""Seasonal TEK calendar alerts endpoint — nested under /api/farms/{farm_id}."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.models import Farm, Field, HealthScore
from cultivos.db.session import get_db
from cultivos.models.seasonal_alert import (
    FieldHealthSummary,
    SeasonalAlertOut,
    SeasonalAlertsResponse,
)
from cultivos.services.intelligence.seasonal_calendar import (
    _classify_current_season,
    generate_seasonal_alerts,
)

router = APIRouter(
    prefix="/api/farms/{farm_id}",
    tags=["seasonal-alerts"],
    dependencies=[Depends(get_current_user)]
)


def _get_farm(farm_id: int, db: Session) -> Farm:
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm


def _get_field_health(db: Session, farm_id: int) -> list[FieldHealthSummary]:
    """Get latest health score per field for a farm."""
    # Subquery: max scored_at per field
    latest_sq = (
        db.query(
            HealthScore.field_id,
            func.max(HealthScore.scored_at).label("max_scored"),
        )
        .join(Field, Field.id == HealthScore.field_id)
        .filter(Field.farm_id == farm_id)
        .group_by(HealthScore.field_id)
        .subquery()
    )

    rows = (
        db.query(Field, HealthScore)
        .join(HealthScore, HealthScore.field_id == Field.id)
        .join(
            latest_sq,
            (HealthScore.field_id == latest_sq.c.field_id)
            & (HealthScore.scored_at == latest_sq.c.max_scored),
        )
        .filter(Field.farm_id == farm_id)
        .all()
    )

    return [
        FieldHealthSummary(
            field_id=field.id,
            field_name=field.name,
            crop_type=field.crop_type,
            score=hs.score,
            trend=hs.trend,
        )
        for field, hs in rows
    ]


@router.get("/seasonal-alerts", response_model=SeasonalAlertsResponse)
def get_seasonal_alerts(
    farm_id: int,
    reference_date: Optional[date] = Query(default=None, description="Override date (defaults to today)"),
    db: Session = Depends(get_db),
):
    """Get seasonal TEK calendar alerts for a farm.

    Returns active planting, preparation, harvest, and maintenance
    windows based on Jalisco phenology and ancestral traditions,
    enriched with current field health scores.
    """
    _get_farm(farm_id, db)

    ref = reference_date or date.today()
    alerts = generate_seasonal_alerts(reference_date=ref)
    season = _classify_current_season(ref.month)

    field_health = _get_field_health(db, farm_id)
    avg_health = None
    if field_health:
        avg_health = round(sum(fh.score for fh in field_health) / len(field_health), 1)

    return SeasonalAlertsResponse(
        farm_id=farm_id,
        season=season,
        reference_date=ref.isoformat(),
        alerts=[SeasonalAlertOut(**a) for a in alerts],
        field_health=field_health,
        avg_health=avg_health,
    )
