"""Drone mission planning endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field
from cultivos.db.session import get_db
from cultivos.models.mission import MissionPlanOut
from cultivos.services.drone.mission import generate_mission_plan

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}",
    tags=["missions"],
)


def _get_field(farm_id: int, field_id: int, db: Session) -> Field:
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(
        Field.id == field_id, Field.farm_id == farm_id,
    ).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@router.get("/mission-plan", response_model=MissionPlanOut)
def get_mission_plan(
    farm_id: int,
    field_id: int,
    mission_type: str = "health_scan",
    drone_type: str = "mavic_multispectral",
    db: Session = Depends(get_db),
):
    field = _get_field(farm_id, field_id, db)
    if not field.boundary_coordinates:
        raise HTTPException(
            status_code=400,
            detail="Field has no boundary coordinates — cannot generate mission plan",
        )
    plan = generate_mission_plan(
        boundary_coordinates=field.boundary_coordinates,
        mission_type=mission_type,
        drone_type=drone_type,
    )
    return MissionPlanOut(**plan)
