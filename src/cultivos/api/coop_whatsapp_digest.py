"""Cooperative WhatsApp digest endpoint (#202).

GET /api/cooperatives/{coop_id}/whatsapp-digest — composes per-farm
whatsapp-status (#185) into a single cooperative digest with top 3 farms
needing attention and a one-line Spanish summary.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.models import Cooperative
from cultivos.db.session import get_db
from cultivos.models.coop_whatsapp_digest import (
    AttentionFarmEntry,
    CoopWhatsAppDigestOut,
)
from cultivos.services.intelligence.coop_whatsapp_digest import (
    compute_coop_whatsapp_digest,
)

router = APIRouter(
    prefix="/api/cooperatives/{coop_id}/whatsapp-digest",
    tags=["intelligence"],
    dependencies=[Depends(get_current_user)]
)


@router.get(
    "",
    response_model=CoopWhatsAppDigestOut,
    description=(
        "Cooperative-wide WhatsApp digest: composes per-farm whatsapp-status "
        "into one Spanish summary with top 3 farms needing attention."
    ),
)
def get_coop_whatsapp_digest(coop_id: int, db: Session = Depends(get_db)):
    coop = db.query(Cooperative).filter(Cooperative.id == coop_id).first()
    if not coop:
        raise HTTPException(status_code=404, detail="Cooperative not found")

    result = compute_coop_whatsapp_digest(coop_id, db)
    return CoopWhatsAppDigestOut(
        cooperative_id=result["cooperative_id"],
        generated_at=result["generated_at"],
        total_farms=result["total_farms"],
        total_critical_alerts=result["total_critical_alerts"],
        total_high_alerts=result["total_high_alerts"],
        farms_with_alerts=result["farms_with_alerts"],
        top_attention_farms=[
            AttentionFarmEntry(**f) for f in result["top_attention_farms"]
        ],
        digest_message_es=result["digest_message_es"],
    )
