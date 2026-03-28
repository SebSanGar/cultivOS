"""Alert configuration endpoints — custom thresholds per farm."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import AlertConfig, Farm
from cultivos.db.session import get_db
from cultivos.models.alert_config import AlertConfigCreate, AlertConfigOut, AlertConfigUpdate

router = APIRouter(
    prefix="/api/farms/{farm_id}/alert-config",
    tags=["alert-config"],
)


def _get_farm(farm_id: int, db: Session) -> Farm:
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm


def get_or_create_config(farm_id: int, db: Session) -> AlertConfig:
    """Return existing config or create one with defaults."""
    config = db.query(AlertConfig).filter(AlertConfig.farm_id == farm_id).first()
    if not config:
        config = AlertConfig(farm_id=farm_id)
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


@router.get("", response_model=AlertConfigOut)
def get_alert_config(
    farm_id: int,
    db: Session = Depends(get_db),
):
    """Get alert configuration for a farm. Returns defaults if none set."""
    _get_farm(farm_id, db)
    config = get_or_create_config(farm_id, db)
    return config


@router.post("", response_model=AlertConfigOut, status_code=201)
def create_alert_config(
    farm_id: int,
    body: AlertConfigCreate,
    db: Session = Depends(get_db),
):
    """Create alert configuration with custom thresholds."""
    _get_farm(farm_id, db)
    # Delete existing if any, then create new
    existing = db.query(AlertConfig).filter(AlertConfig.farm_id == farm_id).first()
    if existing:
        db.delete(existing)
        db.flush()
    config = AlertConfig(
        farm_id=farm_id,
        health_score_floor=body.health_score_floor,
        ndvi_minimum=body.ndvi_minimum,
        temp_max_c=body.temp_max_c,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@router.put("", response_model=AlertConfigOut)
def update_alert_config(
    farm_id: int,
    body: AlertConfigUpdate,
    db: Session = Depends(get_db),
):
    """Update alert configuration — only provided fields are changed."""
    _get_farm(farm_id, db)
    config = get_or_create_config(farm_id, db)
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)
    db.commit()
    db.refresh(config)
    return config
