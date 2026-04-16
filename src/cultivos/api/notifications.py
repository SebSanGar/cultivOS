"""Notification history — log of all alerts/recommendations with acknowledge."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.models import AlertLog, Farm
from cultivos.db.session import get_db
from cultivos.models.alert import AlertLogCreate, AlertLogOut

router = APIRouter(prefix="/api/farms/{farm_id}/notifications", tags=["notifications"], dependencies=[Depends(get_current_user)])


def _get_farm(farm_id: int, db: Session):
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm


@router.post("", response_model=AlertLogOut, status_code=201)
def create_notification(
    farm_id: int,
    payload: AlertLogCreate,
    db: Session = Depends(get_db),
):
    """Create a new notification alert for a farm, specifying type, message, and severity."""
    _get_farm(farm_id, db)
    log = AlertLog(
        farm_id=farm_id,
        field_id=payload.field_id,
        alert_type=payload.alert_type,
        message=payload.message,
        severity=payload.severity,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("", response_model=list[AlertLogOut])
def list_notifications(
    farm_id: int,
    severity: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """List all notifications for a farm, optionally filtered by severity, ordered by most recent."""
    _get_farm(farm_id, db)
    q = db.query(AlertLog).filter(AlertLog.farm_id == farm_id)
    if severity:
        q = q.filter(AlertLog.severity == severity)
    return q.order_by(AlertLog.created_at.desc()).all()


@router.post("/{notification_id}/acknowledge", response_model=AlertLogOut)
def acknowledge_notification(
    farm_id: int,
    notification_id: int,
    db: Session = Depends(get_db),
):
    """Mark a notification as acknowledged by its ID."""
    _get_farm(farm_id, db)
    log = (
        db.query(AlertLog)
        .filter(AlertLog.id == notification_id, AlertLog.farm_id == farm_id)
        .first()
    )
    if not log:
        raise HTTPException(status_code=404, detail="Notification not found")
    log.acknowledged = True
    db.commit()
    db.refresh(log)
    return log
