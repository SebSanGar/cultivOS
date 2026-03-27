"""Alert endpoints — nested under /api/farms/{farm_id}/alerts."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Alert, Farm, Field, HealthScore
from cultivos.db.session import get_db
from cultivos.models.alert import AlertCheckResponse, AlertOut
from cultivos.services.alerts.sms import HEALTH_THRESHOLD, format_sms_message, should_send_alert

router = APIRouter(
    prefix="/api/farms/{farm_id}/alerts",
    tags=["alerts"],
)


def _get_farm(farm_id: int, db: Session) -> Farm:
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm


@router.post("/check", response_model=AlertCheckResponse)
def check_and_create_alerts(
    farm_id: int,
    db: Session = Depends(get_db),
):
    """Check all fields in a farm for low health and create alerts.

    Scans each field's latest health score. If score < 40,
    creates an SMS alert (unless one was sent within 24h).
    """
    farm = _get_farm(farm_id, db)
    fields = db.query(Field).filter(Field.farm_id == farm_id).all()

    alerts_created = []
    for field in fields:
        latest_score = (
            db.query(HealthScore)
            .filter(HealthScore.field_id == field.id)
            .order_by(HealthScore.scored_at.desc())
            .first()
        )
        if not latest_score or latest_score.score >= HEALTH_THRESHOLD:
            continue

        if not should_send_alert(db, farm_id, field.id, "low_health"):
            continue

        message = format_sms_message(
            farm_name=farm.name,
            field_name=field.name,
            alert_type="low_health",
            score=latest_score.score,
        )
        alert = Alert(
            farm_id=farm_id,
            field_id=field.id,
            alert_type="low_health",
            message=message,
            phone_number=None,  # filled when Twilio is configured
            status="pending",
        )
        db.add(alert)
        alerts_created.append(alert)

    if alerts_created:
        db.commit()
        for a in alerts_created:
            db.refresh(a)

    return AlertCheckResponse(
        farm_id=farm_id,
        alerts_created=[AlertOut.model_validate(a) for a in alerts_created],
        fields_checked=len(fields),
    )


@router.get("", response_model=list[AlertOut])
def list_alerts(
    farm_id: int,
    db: Session = Depends(get_db),
):
    """List all alerts for a farm, most recent first."""
    _get_farm(farm_id, db)
    return (
        db.query(Alert)
        .filter(Alert.farm_id == farm_id)
        .order_by(Alert.sent_at.desc())
        .all()
    )
