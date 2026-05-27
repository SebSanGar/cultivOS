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
    """Generate a drone mission plan for a field based on its boundary coordinates, mission type, and drone type."""
    field = _get_field(farm_id, field_id, db)

    # H5 — Graceful degradation: when field has no boundary_coordinates,
    # generate a default 10-ha square plan. Frontend /campo loads this endpoint
    # on page load; a 400 breaks the page even when no flight is planned.
    if not field.boundary_coordinates:
        hectares = field.hectares or 10.0
        # Default square centered on Jalisco (20.5N, -103.5W)
        import math
        clat, clon = 20.5, -103.5
        side_km = math.sqrt(hectares / 100)
        dlat = side_km / 110.6 / 2
        dlon = side_km / (104.5 * math.cos(math.radians(clat))) / 2
        boundary = [
            [round(clon - dlon, 6), round(clat - dlat, 6)],
            [round(clon + dlon, 6), round(clat - dlat, 6)],
            [round(clon + dlon, 6), round(clat + dlat, 6)],
            [round(clon - dlon, 6), round(clat + dlat, 6)],
            [round(clon - dlon, 6), round(clat - dlat, 6)],
        ]
    else:
        boundary = field.boundary_coordinates

    plan = generate_mission_plan(
        boundary_coordinates=boundary,
        mission_type=mission_type,
        drone_type=drone_type,
    )
    return MissionPlanOut(**plan)
