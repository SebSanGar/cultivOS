"""Farm alert escalation backlog endpoint.

GET /api/farms/{farm_id}/alert-escalations?days=30 — lists alerts older than
3 days on the farm with no treatment response. Sorted by days_pending DESC.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.models import Farm
from cultivos.db.session import get_db
from cultivos.models.alert_escalations import (
    AlertEscalationItem,
    FarmAlertEscalationsOut,
)
from cultivos.services.intelligence.alert_escalations import (
    compute_alert_escalations,
)

router = APIRouter(
    prefix="/api/farms/{farm_id}/alert-escalations",
    tags=["alerts"],
    dependencies=[Depends(get_current_user)]
)


@router.get(
    "",
    response_model=FarmAlertEscalationsOut,
    description=(
        "Lists alerts that have been active 3+ days on the farm without a "
        "treatment response. Composes Alert + TreatmentRecord to surface the "
        "actionability gap in the alert->treatment loop. Sorted days_pending "
        "DESC; severity + recommended_action_es derived from alert_type."
    ),
)
def get_farm_alert_escalations(
    farm_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    result = compute_alert_escalations(farm, db, days=days)
    return FarmAlertEscalationsOut(
        farm_id=result["farm_id"],
        days=result["days"],
        total=result["total"],
        escalations=[AlertEscalationItem(**e) for e in result["escalations"]],
    )
